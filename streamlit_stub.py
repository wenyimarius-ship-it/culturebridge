"""最小化的 Streamlit / OpenAI 替身，用来在没有真实 Streamlit 的环境里
把 app.py 整个脚本真正执行一遍（含 rerun、会话状态、缓存装饰器）。

只模拟 app.py 用到的接口；它验证的是“脚本逻辑能跑通、数据流正确”，
不验证真实浏览器里的排版。
"""

import runpy
import types
from collections import defaultdict


class Rerun(Exception):
    pass


class Stop(Exception):
    pass


class Proxy:
    """既是上下文管理器，又把属性转发给 st（用于 col.button / slot.caption 等）。"""

    def __init__(self, st):
        self._st = st

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __getattr__(self, name):
        return getattr(self._st, name)


class FakeStreamlit(types.ModuleType):
    def __init__(self, app_path):
        super().__init__("streamlit")
        self.app_path = app_path
        self.session_state = {}
        self.query_params = {}
        self.secrets = types.SimpleNamespace(get=lambda name, default=None: default)
        self.inputs = {}        # 按 key 或 label 预设控件取值
        self.clicks = set()     # 本次运行中被“点击”的按钮（key 或 label）
        self.out = defaultdict(list)
        self._memo = {}
        self._pending = {}
        self.sidebar = Proxy(self)

        components = types.ModuleType("streamlit.components")
        v1 = types.ModuleType("streamlit.components.v1")
        v1.html = lambda body, **kw: self.out["components_html"].append(body)
        components.v1 = v1
        self.components = components
        self._components_v1 = v1

    # ------------ 运行 ------------
    def run(self, clicks=()):
        self.out = defaultdict(list)
        self.clicks = set(clicks)
        # 按 key 预设的输入只在本次“用户操作”触发的第一轮生效，
        # 之后（含 st.rerun 之后）以会话状态为准，与真实 Streamlit 一致
        self._pending = dict(self.inputs)
        for _ in range(8):
            try:
                runpy.run_path(str(self.app_path), run_name="__main__")
                return
            except Stop:
                return
            except Rerun:
                self.clicks = set()
        raise AssertionError("too many reruns")

    def new_visitor(self):
        self.session_state.clear()
        self.inputs = {}

    # ------------ 缓存装饰器 ------------
    def _cache(self, fn=None, **kw):
        def wrap(func):
            qual = func.__qualname__

            def inner(*args, **kwargs):
                key = (qual, args, tuple(sorted(kwargs.items())))
                if key not in self._memo:
                    self._memo[key] = func(*args, **kwargs)
                return self._memo[key]

            inner.clear = lambda: [self._memo.pop(k) for k in list(self._memo) if k[0] == qual]
            return inner

        return wrap(fn) if callable(fn) else wrap

    cache_resource = property(lambda self: self._cache)
    cache_data = property(lambda self: self._cache)

    # ------------ 输出类 ------------
    def set_page_config(self, **kw): pass
    def subheader(self, *a, **kw): pass
    def header(self, *a, **kw): pass
    def write(self, *a, **kw): self.out["write"].append(a)
    def divider(self): pass
    def code(self, *a, **kw): self.out["code"].append(a[0])
    def progress(self, *a, **kw): pass
    def bar_chart(self, *a, **kw): self.out["bar_chart"].append(a)
    def dataframe(self, *a, **kw): self.out["dataframe"].append(a)
    def metric(self, label, value, **kw): self.out["metric"].append((label, value))
    def caption(self, text, **kw): self.out["caption"].append(text)
    def markdown(self, body, **kw): self.out["markdown"].append(body)
    def info(self, text, **kw): self.out["info"].append(text)
    def warning(self, text, **kw): self.out["warning"].append(text)
    def error(self, text, **kw): self.out["error"].append(text)
    def success(self, text, **kw): self.out["success"].append(text)
    def download_button(self, label, data=None, **kw):
        self.out["download"].append((label, data))
        return False

    # ------------ 布局 ------------
    def columns(self, spec, **kw):
        n = spec if isinstance(spec, int) else len(spec)
        return [Proxy(self) for _ in range(n)]

    def tabs(self, labels):
        return [Proxy(self) for _ in labels]

    def expander(self, *a, **kw): return Proxy(self)
    def spinner(self, *a, **kw): return Proxy(self)
    def form(self, *a, **kw): return Proxy(self)
    def empty(self): return Proxy(self)

    def rerun(self): raise Rerun()
    def stop(self): raise Stop()

    # ------------ 控件 ------------
    def _value(self, label, key, default):
        if key is not None:
            if key in self._pending:
                self.session_state[key] = self._pending.pop(key)
            self.session_state.setdefault(key, default)
            return self.session_state[key]
        return self.inputs.get(label, default)

    def button(self, label, key=None, disabled=False, **kw):
        if disabled:
            return False
        return (key or label) in self.clicks or label in self.clicks

    def form_submit_button(self, label, **kw):
        return label in self.clicks

    def selectbox(self, label, options, index=0, key=None, **kw):
        return self._value(label, key, list(options)[index])

    def radio(self, label, options, index=0, key=None, **kw):
        return self._value(label, key, list(options)[index])

    def multiselect(self, label, options, key=None, **kw):
        return self._value(label, key, [])

    def text_input(self, label, key=None, value="", **kw):
        return self._value(label, key, value)

    def text_area(self, label, key=None, value="", **kw):
        return self._value(label, key, value)

    def checkbox(self, label, key=None, value=False, **kw):
        return self._value(label, key, value)

    def slider(self, label, min_value=0, max_value=100, value=0, key=None, **kw):
        return self._value(label, key, value)


class FakeOpenAIModule(types.ModuleType):
    def __init__(self):
        super().__init__("openai")
        self.responses = []   # 队列：字符串 或 异常实例
        self.calls = []

        class APIConnectionError(Exception): pass
        class APITimeoutError(APIConnectionError): pass
        class AuthenticationError(Exception): pass
        class RateLimitError(Exception): pass

        self.APIConnectionError = APIConnectionError
        self.APITimeoutError = APITimeoutError
        self.AuthenticationError = AuthenticationError
        self.RateLimitError = RateLimitError

        outer = self

        class OpenAI:
            def __init__(self, **kw):
                self.kw = kw
                self.chat = types.SimpleNamespace(
                    completions=types.SimpleNamespace(create=self._create)
                )

            def _create(self, **kw):
                outer.calls.append(kw)
                item = outer.responses.pop(0)
                if isinstance(item, Exception):
                    raise item
                message = types.SimpleNamespace(content=item)
                return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])

        self.OpenAI = OpenAI
