from epi.stage_wiki import _deposition_value, _method_idea


def test_docking_reinforcement_learning_report_prefers_docking_control_over_dpg_tracking():
    metadata = {
        "title": "Docking Control of an Autonomous Underwater Vehicle Using Reinforcement Learning",
        "abstract": (
            "Autonomous underwater vehicles need to autonomously dock onto a charging station. "
            "Reinforcement learning strategies are applied to control docking in simulation. "
            "The paper compares deep deterministic policy gradient (DDPG) and deep Q network (DQN)."
        ),
    }

    method = _method_idea(metadata, metadata["title"])
    deposition = _deposition_value(metadata, metadata["title"], {"claims": []})

    assert "对接控制（Docking Control）" in method
    assert "AUV 对接控制" in deposition
    assert "轨迹跟踪控制" not in method
    assert "Q-learning/DPG 方法对比" not in deposition


def test_mpq_dpg_tracking_report_still_uses_tracking_control_bucket():
    metadata = {
        "title": (
            "Multi Pseudo Q-learning Based Deterministic Policy Gradient for Tracking Control "
            "of Autonomous Underwater Vehicles"
        ),
        "abstract": (
            "This paper investigates trajectory tracking for underactuated autonomous underwater "
            "vehicles using Multi Pseudo Q-learning and deterministic policy gradient."
        ),
    }

    method = _method_idea(metadata, metadata["title"])
    deposition = _deposition_value(metadata, metadata["title"], {"claims": []})

    assert "跟踪控制" in method
    assert "Q-learning/DPG 方法对比" in deposition
