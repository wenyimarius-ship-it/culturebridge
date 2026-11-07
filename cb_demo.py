"""Authored examples, never model output or automatically verified facts."""
LENS = {
    "ritual": {"en": "Chinese tea preparation includes varied practices. Gongfu tea is one approach involving care with tea, water and repeated infusions; it is not a rule for every household.", "zh": "中国泡茶方式多样。功夫茶是注重茶、水及多次冲泡的一种实践，并非每个家庭都遵循的规则。"},
    "hospitality": {"en": "Tea can be part of welcoming guests in Chinese social settings. The meaning and etiquette vary by place, occasion and person.", "zh": "茶可以是中国社会情境中迎接客人的一部分，其含义与礼节因地域、场合及个人而异。"},
    "details": {"en": "Tea type, water and teaware can shape a tea-drinking experience. Avoid presenting one brewing method as the authentic method for all Chinese teas.", "zh": "茶类、水与茶具会影响饮茶体验。不要把某一种泡法当成所有中国茶唯一的正宗方式。"},
    "connect": {"en": "Sharing tea can create an occasion for conversation. This is a possible social meaning, not a claim that every tea drinker experiences it in the same way.", "zh": "分享茶可以提供交谈的机会。这是一种可能的社会意义，不代表每位饮茶者都有同样体验。"},
    "cuppa": {"en": "Some Chinese teas are enjoyed without milk. Chinese and British tea practices both vary; neither should be treated as a single uniform tradition.", "zh": "部分中国茶不加奶饮用。中国与英国的饮茶实践都存在差异，不宜把任何一方概括为单一传统。"},
}
SCENES = {
    "ritual": ("Watch the leaves open, then give the next pour your attention.", "看茶叶舒展，把注意力留给下一次注水。"),
    "hospitality": ("Put a spare cup on the table and invite a colleague to join you.", "在桌上多放一只杯子，邀请同事一起喝茶。"),
    "details": ("Try the same tea twice and notice what changes in the cup.", "尝两次同一种茶，留意杯中的变化。"),
    "connect": ("Set two cups between you and let a conversation take its time.", "在彼此之间放两只杯子，让谈话慢慢展开。"),
    "cuppa": ("Usually reach for milk? Try a sip of Chinese tea on its own and notice the flavour.", "平时习惯加奶？试着单独品一口中国茶，留意它的风味。"),
}
OPENERS = {
    "curious": ("What could a different tea break feel like?", "换一种茶歇，会有什么感受？"),
    "playful": ("Your inbox can wait for one sip.", "让收件箱等你喝一口。"),
    "reflective": ("A small pause can be an invitation to pay attention.", "短暂的停顿，也可以是留心当下的邀请。"),
}


def demo_result(angle, platform, style):
    opening, opening_zh = OPENERS[style]
    scene, scene_zh = SCENES[angle]
    ending = "Who would you invite for a tea break at work?" if platform == "LinkedIn" else "What would you notice in your next cup?"
    ending_zh = "你会邀请谁一起在工作间隙喝杯茶？" if platform == "LinkedIn" else "下一杯茶，你会留意什么？"
    post = f"{opening} {scene} Exploring Chinese tea culture can start with curiosity rather than a list of rules. {ending}"
    if platform == "Instagram":
        post += " #TeaCulture"
    return (f"【English Post】\n{post}\n【中文翻译】\n{opening_zh}{scene_zh}以好奇心开始探索中国茶文化，而不是先记一串规则。{ending_zh}"
            "\n【文化表达思路】\n人工编写的示例：用具体茶歇场景邀请英国年轻职场人参与，不将个别做法泛化为所有中国人的习惯。风格和平台只改变示例模板；不会处理自由文本改写要求。"
            "\n【需要核实的内容】\n- 核对文化背景中涉及的茶类、冲泡与社交实践，不能据此推断所有人的习惯。\n- 将文案用于具体地域或茶类前，核对其适用情境。")
