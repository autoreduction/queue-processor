# reduction_viewer_datalocation
INSERT INTO reduction_viewer_datalocation
    (id, file_path, reduction_run_id)
VALUES
    (1, 'test/file/path/1.raw', 001),
    (2, 'test/file/path/2.raw', 002),
    (3, 'test/file/path/3.raw', 003);

# ======================================= #
# reduction_viewer_experiment
INSERT INTO reduction_viewer_experiment
    (id, reference)
VALUES
    (1, 123),
    (2, 456),
    (3, 789);

# ======================================= #
# reduction_viewer_instrument
INSERT INTO reduction_viewer_instrument
    (id, name, is_active, is_paused)
VALUES
    (1, 'TEST', 0, 0),
    (2, 'WISH', 0, 0),
    (3, 'GEM', 0, 0);

# ======================================= #
# reduction_viewer_notification
INSERT INTO reduction_viewer_notification
    (id, message, is_active, severity, is_staff_only)
VALUES
    (),
    (),
    ();

# ======================================= #
# reduction_viewer_reductionlocation
INSERT INTO reduction_viewer_reductionlocation
    (id, file_path, reduction_run_id)
VALUES
    (1, 'path/to/reduced/data/1', 001),
    (2, 'path/to/reduced/data/2', 002),
    (3, 'path/to/reduced/data/3', 003);

# ======================================= #
# reduction_viewer_reductionrun
INSERT INTO reduction_viewer_reductionrun
    (id, run_number, run_version, run_name, script, created, last_updated, started, finished, started_by, graph, message, reduction_log, admin_log, retry_when, cancel, hidden_in_failviewer, overwrite, experiment_id, instrument_id, retry_run_id, status_id)
VALUES
    (1, 001, 0, 'test-run', 'print("running test run")', '2018-10-04 09:00:00', '2018-10-04 09:00:00', '2018-10-04 09:00:00', '2018-10-04 09:01:00', NULL, NULL, '', '', '', NULL, NULL, 0, 0, NULL, 1, 1, 4)
    (2, 002, 0, 'test-run', 'print("running test run")', '2018-10-04 09:02:00', '2018-10-04 09:02:00', '2018-10-04 09:02:00', '2018-10-04 09:03:00', NULL, NULL, '', '', '', NULL, NULL, 0, 0, NULL, 2, 2, 4)
    (3, 003, 0, 'test-run', 'print("running test run")', '2018-10-04 09:04:00', '2018-10-04 09:04:00', '2018-10-04 09:04:00', '2018-10-04 09:05:00', NULL, NULL, '', '', '', NULL, NULL, 0, 0, NULL, 3, 3, 4);

# ======================================= #
# reduction_viewer_setting
INSERT INTO reduction_viewer_setting
    (id, name, value)
VALUES
    (),
    (),
    ();

# ======================================= #
# reduction_viewer_status
INSERT INTO reduction_viewer_status
    (id, value)
VALUES
    (1, 'Error'),
    (2, 'Queued'),
    (3, 'Processing'),
    (4, 'Completed'),
    (5, 'Skipped');
