// kintai/static/kintai/script.js

document.addEventListener('DOMContentLoaded', () => {
    console.log('Script loaded successfully');
    
    // 期間選択ボタンのフォントサイズを強制的に設定
    const periodButtons = document.querySelectorAll('.period-btn[data-months]');
    console.log('Found period buttons:', periodButtons.length);
    
    // ボタンコンテナのグリッドレイアウトを強制設定
    const periodButtonsContainer = document.querySelector('.period-buttons');
    if (periodButtonsContainer) {
        console.log('Setting grid layout for period buttons container');
        periodButtonsContainer.style.cssText = `
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 12px !important;
            max-width: 360px !important;
            margin: 0 auto !important;
            justify-content: center !important;
            align-items: center !important;
        `;
    }

    // 期間ボタンのアクティブ状態管理
    const currentUrl = window.location.href;
    const urlParams = new URLSearchParams(window.location.search);
    const currentMonths = urlParams.get('months') || '3'; // デフォルトは3ヶ月

    periodButtons.forEach((button, index) => {
        console.log(`Setting font size and height for button ${index}:`, button.textContent);
        
        const buttonMonths = button.getAttribute('data-months');
        const isActive = buttonMonths === currentMonths;
        
        // インラインスタイルで直接設定（最強の方法）
        button.style.cssText = `
            font-size: 0.9em !important;
            height: 40px !important;
            min-height: 40px !important;
            max-height: 40px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 8px 16px !important;
            line-height: 1.0 !important;
            box-sizing: border-box !important;
            width: 170px !important;
            margin: 1px !important;
            border-radius: 6px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            font-weight: 500 !important;
            background: ${isActive ? '#2563eb' : '#ffffff'} !important;
            border: 1px solid ${isActive ? '#2563eb' : '#d1d5db'} !important;
            color: ${isActive ? '#ffffff' : '#374151'} !important;
            box-shadow: ${isActive ? '0 4px 12px rgba(37, 99, 235, 0.3)' : 'none'} !important;
            transform: ${isActive ? 'translateY(-1px)' : 'none'} !important;
        `;
        
        // アクティブクラスの追加/削除
        if (isActive) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
            // ハンバーガーメニューとサイドバーの機能
            const hamburgerMenu = document.getElementById('hamburgerMenu');
            const sidebar = document.getElementById('sidebar');
            const sidebarOverlay = document.getElementById('sidebarOverlay');
            const sidebarCloseButton = document.getElementById('sidebarCloseButton');

            console.log('Elements found:', { hamburgerMenu, sidebar, sidebarOverlay, sidebarCloseButton });

            if (hamburgerMenu && sidebar && sidebarOverlay) {
                console.log('All elements found, setting up event listeners');

                // サイドバーを閉じる関数
                const closeSidebar = () => {
                    console.log('Closing sidebar');
                    sidebar.classList.remove('open');
                    sidebarOverlay.classList.remove('active');
                    hamburgerMenu.classList.remove('active');
                };

                // ハンバーガーメニューをクリックした時の処理
                hamburgerMenu.addEventListener('click', () => {
                    console.log('Hamburger menu clicked');
                    console.log('Sidebar classes before:', sidebar.className);
                    sidebar.classList.toggle('open');
                    sidebarOverlay.classList.toggle('active');
                    hamburgerMenu.classList.toggle('active');
                    console.log('Sidebar classes after:', sidebar.className);
                    console.log('Sidebar computed style:', window.getComputedStyle(sidebar).right);
                });

                // サイドバーの閉じるボタンをクリックした時の処理
                if (sidebarCloseButton) {
                    sidebarCloseButton.addEventListener('click', () => {
                        console.log('Sidebar close button clicked');
                        closeSidebar();
                    });
                }

                // オーバーレイをクリックした時の処理（サイドバーを閉じる）
                sidebarOverlay.addEventListener('click', () => {
                    console.log('Overlay clicked');
                    closeSidebar();
                });

                // ESCキーでサイドバーを閉じる
                document.addEventListener('keydown', (event) => {
                    if (event.key === 'Escape' && sidebar.classList.contains('open')) {
                        console.log('ESC key pressed');
                        closeSidebar();
                    }
                });
            } else {
                console.error('Some elements not found:', { hamburgerMenu, sidebar, sidebarOverlay, sidebarCloseButton });
            }

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
        
        // ファイル選択ダイアログを無効化（カメラのみ有効）
        photoInput.addEventListener('click', (event) => {
            // モバイルデバイスではcapture属性によりカメラが優先される
            console.log('ファイル入力がクリックされました - カメラを起動します');
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