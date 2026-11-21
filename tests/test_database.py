from campuslink.database.store import Database, Profile


def test_profile_round_trip(tmp_path):
    database = Database(tmp_path / "test.db")
    database.initialize()
    profile = Profile("Ada", "ada@example.edu", "Engineering", "3", "Laptop")
    database.save_profile(profile)
    assert database.get_profile() == profile
    database.close()


def test_blank_display_name_is_rejected(tmp_path):
    database = Database(tmp_path / "test.db")
    database.initialize()
    try:
        database.save_profile(Profile("  "))
    except ValueError:
        pass
    else:
        raise AssertionError("blank name accepted")


def test_chat_history_and_delivery_state(tmp_path):
    database = Database(tmp_path / "test.db")
    database.initialize()
    message_id = database.save_chat_message(
        "peer-1", "Grace", "outgoing", "Hello", "queued"
    )
    database.update_message_status(message_id, "delivered")
    history = database.chat_history("peer-1")
    assert len(history) == 1
    assert history[0].body == "Hello"
    assert history[0].status == "delivered"
    database.close()
