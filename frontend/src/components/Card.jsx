import styles from "./Card.module.css";

// variant: feature (surface-card) | product (canvas+hairline) | plain.
export default function Card({ variant = "feature", className = "", ...props }) {
  return (
    <div className={`${styles.card} ${styles[variant]} ${className}`} {...props} />
  );
}
