"""Optional real-browser smoke test. Run against an isolated, Chinese, no-key Demo server."""
import argparse
import csv
import shutil
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='http://127.0.0.1:8501')
parser.add_argument('--artifacts', default=tempfile.mkdtemp(prefix='culturebridge-browser-'))
args = parser.parse_args()
artifacts = Path(args.artifacts)
artifacts.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('chromium'), headless=True)
    context=browser.new_context(viewport={'width':390,'height':844},permissions=['clipboard-read','clipboard-write'])
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.goto(args.url)
    generate=page.get_by_role('button',name='✨ 生成文化短帖')
    generate.click(timeout=30000)
    page.locator('.post-body').wait_for()
    post=page.locator('.post-body').inner_text()
    assert 'Demo 示例' in page.locator('body').inner_text()
    frame=page.frame_locator('iframe').first
    frame.get_by_role('button',name='📋 复制英文短帖').click()
    page.wait_for_timeout(500)
    copied=page.evaluate('navigator.clipboard.readText()')
    assert copied==post,repr(copied)
    print('PASS mobile Demo generation and clipboard exact text')
    page.get_by_role('tab',name='03 / Cultural Lens').click()
    assert page.get_by_text('当前版本尚未完成核验。',exact=True).is_visible()
    assert page.get_by_role('link',name='1. Smithsonian: Tea Culture in China').count() or page.locator('a[href*="asia.si.edu"]').count()
    page.get_by_role('button',name='保存本次审核记录').click()
    page.get_by_text('审核记录已保存。',exact=True).wait_for()
    print('PASS pending cultural review and reference links')
    page.get_by_role('tab',name='04 / Audience Lab').click()
    page.get_by_text('当面测试：直接在本页填写',exact=True).click()
    page.get_by_role('textbox',name='你希望进一步了解什么？（选填）').fill('Mobile phase 3.4 feedback')
    page.get_by_text('我同意将本次匿名评价用于 CultureBridge Demo 的内容改进。',exact=True).click()
    assert page.get_by_role('checkbox',name='我同意将本次匿名评价用于 CultureBridge Demo 的内容改进。').is_checked()
    page.get_by_role('button',name='提交匿名评价',exact=True).click()
    page.get_by_text('感谢你的反馈！匿名评价已保存。',exact=True).wait_for()
    with page.expect_download() as dl:
        page.get_by_role('button',name='导出本次会话的反馈 CSV').click()
    dl.value.save_as(str(artifacts / 'feedback.csv'))
    with (artifacts / 'feedback.csv').open(encoding='utf-8-sig') as exported:
        rows=list(csv.DictReader(exported))
    assert rows[-1]['post_text']==post and rows[-1]['respect']=='3' and rows[-1]['comment']=='Mobile phase 3.4 feedback'
    print('PASS mobile feedback consent, save, Respect and private CSV download')
    page.get_by_role('tab',name='📊 反馈概览').click()
    page.get_by_test_id('stMetric').filter(has_text='平均文化尊重感').wait_for()
    for width in (390,360,1280):
        page.set_viewport_size({'width':width,'height':844})
        page.wait_for_timeout(250)
        dimensions=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
        assert dimensions['scroll']<=dimensions['width'],dimensions
        page.screenshot(path=str(artifacts / f'culturebridge-{width}.png'),full_page=True)
    print('PASS no document overflow at 360, 390 and 1280 pixels')
    assert not errors,errors
    print('PASS no browser page errors')
    browser.close()
