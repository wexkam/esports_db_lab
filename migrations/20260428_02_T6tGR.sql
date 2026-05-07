INSERT INTO team (title, coach, region, foundation_date) VALUES 
('NaVi', 'B1ad3', 'CIS', '2009-12-17'), ('FaZe', 'NEO', 'EU', '2010-05-30'),
('Spirit', 'hally', 'CIS', '2015-06-09'), ('G2', 'TaZ', 'EU', '2013-10-15'),
('Vitality', 'XTQZZZ', 'EU', '2018-10-08'), ('Astralis', 'casle', 'EU', '2016-01-18'),
('Cloud9', 'groove', 'NA', '2014-04-06'), ('MOUZ', 'sycrone', 'EU', '2002-04-01'),
('Virtus.pro', 'dastan', 'CIS', '2003-11-01'), ('Heroic', 'sAw', 'EU', '2016-08-26');

INSERT INTO player (nickname, full_name, role) VALUES 
('s1mple', 'A. Kostyliev', 'AWP'), ('donk', 'D. Kryshkovets', 'Rifler'),
('m0NESY', 'I. Osipov', 'AWP'), ('ZywOo', 'M. Herbaut', 'AWP'),
('NiKo', 'N. Kovac', 'Rifler'), ('ropz', 'R. Kool', 'Lurker'),
('sh1ro', 'D. Sokolov', 'AWP'), ('b1t', 'V. Vakhovskiy', 'Rifler'),
('electroNic', 'D. Sharipov', 'IGL'), ('twistzz', 'R. Van Dulken', 'Rifler');

INSERT INTO match (team_id, match_code, stage, result_1, result_2, maps) VALUES 
(1, 'M1', 'Final', 2, 0, 'Mirage'), (2, 'M2', 'Semi', 1, 2, 'Nuke'),
(3, 'M3', 'Quarter', 2, 1, 'Vertigo'), (4, 'M4', 'Groups', 16, 14, 'Inferno'),
(5, 'M5', 'Final', 2, 1, 'Dust2'), (1, 'M6', 'Groups', 2, 0, 'Anubis'),
(6, 'M7', 'Play-off', 0, 2, 'Ancient'), (7, 'M8', 'Semi', 2, 0, 'Overpass'),
(8, 'M9', 'Grand Final', 3, 2, 'Nuke'), (9, 'M10', 'Quarter', 2, 0, 'Vertigo');

INSERT INTO player_team (player_id, team_id, join_date, departure_date) VALUES 
(1, 1, '2016-08-04', NULL), (2, 3, '2021-08-01', NULL),
(3, 4, '2022-01-03', NULL), (4, 5, '2018-10-08', NULL),
(5, 4, '2020-10-28', NULL), (6, 2, '2022-01-03', NULL),
(7, 3, '2023-12-17', NULL), (8, 1, '2020-12-20', NULL),
(9, 7, '2023-04-15', '2024-01-01'), (10, 2, '2021-01-01', '2023-12-01');

