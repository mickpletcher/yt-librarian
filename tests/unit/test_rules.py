from youtube_knowledge_manager.classification.rules import RulesEngine
from youtube_knowledge_manager.classification.schemas import ClassificationInput, RuleConfig


def test_rule_can_assign_multiple_categories() -> None:
    engine = RulesEngine(
        [
            RuleConfig(
                name="powershell",
                priority=10,
                any_keywords=["PowerShell"],
                categories=["software", "automation"],
                confidence=0.9,
            )
        ]
    )

    decisions = engine.classify(
        ClassificationInput(youtube_video_id="abc", title="PowerShell at scale")
    )

    assert [decision.category_slug for decision in decisions] == ["software", "automation"]
    assert decisions[0].is_primary is True


def test_rule_requires_each_configured_match_group() -> None:
    engine = RulesEngine(
        [
            RuleConfig(
                name="channel-and-keyword",
                any_keywords=["solar"],
                channels=["Practical Engineering"],
                categories=["home"],
                confidence=0.8,
            )
        ]
    )

    decisions = engine.classify(
        ClassificationInput(
            youtube_video_id="abc",
            title="Solar design",
            channel_name="A different channel",
        )
    )

    assert decisions == []
