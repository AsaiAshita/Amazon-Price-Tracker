const express = require('express');
const Database = require('better-sqlite3');
const path = require('path');
const fetch = require('node-fetch'); // for fetching pages
const cheerio = require('cheerio');

const app = express();
const port = 3000;

app.use(express.static(path.join(__dirname, 'public')));

const db = new Database(path.join(__dirname, '..', 'data', 'amazon_price_history.db'), { readonly: true });
console.log('Connected to SQLite database using better-sqlite3');

//endpoint for getting elements from the database
app.get('/elements', (req, res) => {
  console.log("GET /elements hit");
  try {
    const rows = db.prepare(`
      SELECT name AS title, MIN(price) AS lowest_price, link, date, image_link, id
      FROM products
      GROUP BY name
    `).all();
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

//endpoint for getting price history for a product
app.get('/history/:product_id', (req, res) => {
  try {
    const rows = db.prepare(`
      SELECT price, timestamp
      FROM history
      WHERE product_id = ?
      ORDER BY timestamp ASC
    `).all(req.params.product_id);

    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(port, () => console.log(`Server running at http://localhost:${port}`));
