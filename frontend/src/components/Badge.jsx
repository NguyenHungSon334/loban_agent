import styles from "./Badge.module.css";

// tone: default | success | error | warning | orange | accent.
export default function Badge({ tone = "default", className = "", ...props }) {
  return (
    <span className={`${styles.badge} ${styles[tone]} ${className}`} {...props} />
  );
}
