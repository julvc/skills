const express = require("express");
const productos = require("./routes/productos");
const app = express();
app.use(express.json());
app.use("/api/productos", productos);
app.listen(3000);
