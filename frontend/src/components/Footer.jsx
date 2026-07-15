import styles from "./Footer.module.css";

// footer dark đóng trang (DESIGN.md — surface dark duy nhất).
export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.inner}`}>
        <div className={styles.brand}>Hồn Đá — thổi hồn vào đá</div>
        <p className={styles.note}>
          Công cụ nội bộ đối chiếu kích thước Lỗ Ban. Kết quả "Cần xác nhận" phải
          kiểm tra lại trên bản vẽ kỹ thuật trước khi thi công.
        </p>
      </div>
    </footer>
  );
}
