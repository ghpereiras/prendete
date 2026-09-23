import { useAuth } from "../context/AuthContext";

export default function Home() {
  const { user, logout } = useAuth();

  return (
    <div className="page">
      <h1>Hola, {user?.full_name}</h1>
      <p>{user?.email}</p>
      <button onClick={logout}>Cerrar sesión</button>
    </div>
  );
}
