CREATE TABLE IF NOT EXISTS sponsors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_name TEXT NOT NULL,
    product_name TEXT NOT NULL,
    product_description TEXT NOT NULL,
    product_picture TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    ingredient_score REAL DEFAULT 0
);

CREATE VIRTUAL TABLE IF NOT EXISTS ingredients_spell USING spellfix1;

CREATE TRIGGER IF NOT EXISTS trg_ingredients_insert
AFTER INSERT ON ingredients
BEGIN
    INSERT INTO ingredients_spell(word) VALUES (NEW.name);
END;

CREATE TRIGGER IF NOT EXISTS trg_ingredients_update
AFTER UPDATE OF name ON ingredients
BEGIN
    DELETE FROM ingredients_spell WHERE word = OLD.name;
    INSERT INTO ingredients_spell(word) VALUES (NEW.name);
END;

CREATE TRIGGER IF NOT EXISTS trg_ingredients_delete
AFTER DELETE ON ingredients
BEGIN
    DELETE FROM ingredients_spell WHERE word = OLD.name;
END;
