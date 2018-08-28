USE autoreduction;
# ======================================= #
# CONSTANT reduction_viewer_status
INSERT INTO reduction_viewer_status
    (id, value)
VALUES
    (1, 'Error'),
    (2, 'Queued'),
    (3, 'Processing'),
    (4, 'Completed'),
    (5, 'Skipped');
