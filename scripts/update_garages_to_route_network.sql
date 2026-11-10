-- Align the 12 seeded garage names with the existing route network.
-- Run against the selected fleet database; IDs, capacities and truck assignments stay unchanged.
UPDATE garages SET City = 'Riihimäki' WHERE GarageID = 1;
UPDATE garages SET City = 'Helsinki' WHERE GarageID = 2;
UPDATE garages SET City = 'Tampere' WHERE GarageID = 3;
UPDATE garages SET City = 'Turku' WHERE GarageID = 4;
UPDATE garages SET City = 'Oulu' WHERE GarageID = 5;
UPDATE garages SET City = 'Jyväskylä' WHERE GarageID = 6;
UPDATE garages SET City = 'Vaasa' WHERE GarageID = 7;
UPDATE garages SET City = 'Lahti' WHERE GarageID = 8;
UPDATE garages SET City = 'Kotka' WHERE GarageID = 9;
UPDATE garages SET City = 'Kouvola' WHERE GarageID = 10;
UPDATE garages SET City = 'Kuopio' WHERE GarageID = 11;
UPDATE garages SET City = 'Rovaniemi' WHERE GarageID = 12;
