const router = require("express").Router();
const db = [];
router.get("/", (req, res) => res.json(db));
router.post("/", (req, res) => { db.push(req.body); res.status(201).json(req.body); });
router.delete("/:id", (req, res) => res.status(204).end());
module.exports = router;
