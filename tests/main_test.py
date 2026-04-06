from stock_scanner import main as main_module


def test_main_runs(monkeypatch, capsys):
    calls = []

    def fake_download(config, marker, stage):
        calls.append(("download", stage))

    def fake_scan(profile):
        calls.append(("scan", profile))

    monkeypatch.setattr(main_module, "run_download", fake_download)
    monkeypatch.setattr(main_module, "run_scan", fake_scan)

    main_module.main()

    assert len(calls) == 6

    captured = capsys.readouterr()
    assert "DONE" in captured.out