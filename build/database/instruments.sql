USE autoreduction;
# ======================================= #
# CONSTANT reduction_viewer_instrument

INSERT INTO reduction_viewer_instrument
    (id, name, is_active, is_paused)
VALUES
    (1, 'GEM', 1, 0),
    (2, 'WISH', 1, 0),
    (3, 'OSIRIS', 0, 0),
    (4, 'POLARIS', 0, 0),
    (5, 'MUSR', 0, 0),
    (6, 'POLREF', 0, 0);
