export default function ProductCard({ nombre, precio, onAgregar }) {
  return (
    <div className="card">
      <h3>{nombre}</h3>
      <p>${precio}</p>
      <button onClick={() => onAgregar(nombre)}>Agregar</button>
    </div>
  );
}
