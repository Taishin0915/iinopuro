// kintai/static/kintai/script.js

document.addEventListener('DOMContentLoaded', () => {
    const photoInput = document.getElementById('photo-upload-input');
    const previewImage = document.getElementById('preview-image');
    const cameraButton = document.getElementById('camera-button');
    
    // ファイル選択に関連する不要な要素を削除 - テスト中: コメントアウト
    /*
    const removeFileSelectionElements = () => {
        // ファイル選択ボタンを探して削除
        const fileButtons = document.querySelectorAll('button:contains("ファイル選択"), input[type="file"]:not(#photo-upload-input)');
        fileButtons.forEach(btn => {
            if (btn.id !== 'photo-upload-input') {
                btn.style.display = 'none';
                btn.remove();
            }
        });
        
        // "選択されていません"テキストを削除
        const noSelectionTexts = document.querySelectorAll('*');
        noSelectionTexts.forEach(element => {
            if (element.textContent && element.textContent.includes('選択されていません')) {
                element.style.display = 'none';
                element.remove();
            }
        });
        
        // ファイル選択に関連するラベルを削除
        const fileLabels = document.querySelectorAll('label:not([for="photo-upload-input"])');
        fileLabels.forEach(label => {
            if (label.textContent && label.textContent.includes('ファイル選択')) {
                label.style.display = 'none';
                label.remove();
            }
        });
    };
    
    // ページ読み込み時に不要な要素を削除
    removeFileSelectionElements();
    
    // 少し遅延して再度実行（Djangoが動的に要素を追加する場合に対応）
    setTimeout(removeFileSelectionElements, 100);
    */
    
    // カメラボタンがクリックされた時の処理
    if (cameraButton && photoInput) {
        cameraButton.addEventListener('click', () => {
            // 隠れたファイル入力要素をクリックしてカメラを起動
            photoInput.click();
            console.log('カメラアプリを起動します');
        });
    }
    
    // 撮影完了時の処理
    if (photoInput) {
        photoInput.addEventListener('change', (event) => {
            const file = event.target.files[0];

            if (file) {
                // FileReaderを使って撮影された画像を読み込む
                const reader = new FileReader();
                
                // 画像の読み込みが完了したら、プレビュー用のimgタグのsrcを更新
                reader.onload = (e) => {
                    previewImage.src = e.target.result;
                    previewImage.style.width = '200px';
                    previewImage.style.height = '150px';
                    previewImage.style.objectFit = 'cover';
                    console.log('写真が撮影されました');
                };
                
                reader.readAsDataURL(file);
            }
        });
    }
});