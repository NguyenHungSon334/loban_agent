import styles from "./Button.module.css";

// variant: primary (đen) | secondary (trắng+hairline). as: "button" | "a".
export default function Button({
  variant = "primary",
  as = "button",
  className = "",
  ...props
}) {
  const Tag = as;
  return (
    <Tag className={`${styles.btn} ${styles[variant]} ${className}`} {...props} />
  );
}
