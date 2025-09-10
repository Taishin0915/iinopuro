// kintai/static/kintai/script.js

document.addEventListener('DOMContentLoaded', () => {
    const photoInput = document.getElementById('photo-upload-input');
    const previewImage = document.getElementById('preview-image');
    
    // 撮影/ファイル選択ボタンが変更されたときの処理
    photoInput.addEventListener('change', (event) => {
        const file = event.target.files[0];

        if (file) {
            // FileReaderを使って選択された画像を読み込む
            const reader = new FileReader();
            
            // 画像の読み込みが完了したら、プレビュー用のimgタグのsrcを更新
            reader.onload = (e) => {
                previewImage.src = e.target.result;
            };
            
            reader.readAsDataURL(file);
        }
    });
});