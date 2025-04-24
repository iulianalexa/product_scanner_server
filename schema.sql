CREATE TABLE IF NOT EXISTS sponsors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_name TEXT NOT NULL,
    product_name TEXT NOT NULL,
    product_description TEXT NOT NULL,
    product_picture TEXT NOT NULL
);
