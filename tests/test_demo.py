from itertools import product
import cb_core as core
from cb_demo import demo_result


def test_all_authored_combinations_have_complete_reviewable_content():
    for angle, platform, style in product(
        ['ritual', 'hospitality', 'details', 'connect', 'cuppa'],
        ['Instagram', 'LinkedIn'], ['curious', 'playful', 'reflective']
    ):
        post, translation, strategy, review = core.parse_result(demo_result(angle, platform, style))
        assert 10 < core.count_words(post) < 100
        assert translation and strategy and len(core.extract_claims(review)) == 2
