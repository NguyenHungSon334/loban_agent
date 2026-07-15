import { forwardRef } from "react";
import styles from "./TextInput.module.css";

// forwardRef -> dùng thẳng với react-hook-form register(). multiline -> textarea.
const TextInput = forwardRef(function TextInput(
  { label, error, multiline = false, className = "", ...props },
  ref,
) {
  const Field = multiline ? "textarea" : "input";
  return (
    <label className={`${styles.wrap} ${className}`}>
      {label && <span className={styles.label}>{label}</span>}
      <Field
        ref={ref}
        className={`${styles.input} ${error ? styles.invalid : ""}`}
        {...props}
      />
      {error && <span className={styles.error}>{error}</span>}
    </label>
  );
});

export default TextInput;
