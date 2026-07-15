import { NavLink } from "react-router-dom";
import styles from "./TopNav.module.css";

const links = [
  { to: "/", label: "Phân tích", end: true },
  { to: "/ho-so", label: "Hồ sơ" },
  { to: "/thuoc", label: "Thước" },
];

export default function TopNav() {
  return (
    <header className={styles.nav}>
      <div className={`container ${styles.inner}`}>
        <NavLink to="/" className={styles.brand}>
          Hồn Đá<span className={styles.dot}>·</span>Lỗ Ban
        </NavLink>
        <nav className={styles.links}>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                isActive ? `${styles.link} ${styles.active}` : styles.link
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
