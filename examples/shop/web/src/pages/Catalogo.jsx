import { useEffect, useState } from "react";
import ProductCard from "../components/ProductCard";
export default function Catalogo() {
  const [productos, setProductos] = useState([]);
  useEffect(() => { fetch("/api/productos").then(r => r.json()).then(setProductos); }, []);
  return productos.map(p => <ProductCard key={p.nombre} {...p} onAgregar={n => console.log(n)} />);
}
