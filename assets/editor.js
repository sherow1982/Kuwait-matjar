/**
 * محرر TinyMCE لمتجر الكويت
 * محرر عربي متخصص للمتاجر الكويتية
 */

// تحميل TinyMCE
function loadTinyMCE() {
  if (window.tinymce) return Promise.resolve();
  
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/tinymce@7/tinymce.min.js';
    script.crossOrigin = 'anonymous';
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// إعداد محرر متجر الكويت
function initKuwaitMatjarEditor() {
  const config = {
    selector: '.kuwait-editor, .product-text, textarea.kw-editor',
    
    plugins: [
      'autolink', 'autoresize', 'autosave', 'charmap', 'directionality',
      'emoticons', 'fullscreen', 'image', 'link', 'lists', 'media',
      'preview', 'quickbars', 'save', 'table', 'visualblocks', 'wordcount'
    ].join(' '),
    
    toolbar: [
      'undo redo | bold italic underline | fontsize',
      'forecolor backcolor | alignleft aligncenter alignright | ltr rtl',
      'bullist numlist | link image table | preview fullscreen'
    ].join(' | '),
    
    menubar: 'edit view insert format table',
    
    // إعدادات عربية
    directionality: 'rtl',
    language: 'ar',
    
    height: 380,
    resize: 'vertical',
    
    branding: false,
    promotion: false,
    
    // حفظ تلقائي
    autosave_interval: '30s',
    autosave_retention: '25m',
    
    content_style: `
      body {
        font-family: 'Cairo', 'Noto Sans Arabic', Arial, sans-serif;
        font-size: 14px;
        line-height: 1.6;
        direction: rtl;
        text-align: right;
        color: #2c3e50;
      }
      .kuwait-product {
        background: #e8f5e8;
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 15px;
        margin: 12px 0;
        position: relative;
      }
      .kuwait-product:before {
        content: '🇰🇼';
        position: absolute;
        top: 5px;
        right: 5px;
        font-size: 16px;
      }
      .price-kwd {
        background: linear-gradient(45deg, #17a2b8, #20c997);
        color: white;
        padding: 6px 12px;
        border-radius: 15px;
        font-weight: bold;
        display: inline-block;
      }
      .kuwait-special {
        background: #fff3cd;
        border: 1px solid #ffc107;
        padding: 8px 12px;
        border-radius: 6px;
        color: #856404;
        font-weight: bold;
      }
    `,
    
    style_formats: [
      {
        title: 'أنماط المتجر الكويتي',
        items: [
          { title: 'بطاقة منتج كويتي', block: 'div', classes: 'kuwait-product' },
          { title: 'سعر بالدينار', inline: 'span', classes: 'price-kwd' },
          { title: 'عرض خاص', inline: 'span', classes: 'kuwait-special' },
          { title: 'عنوان كويتي', block: 'h3', styles: { color: '#17a2b8' } }
        ]
      }
    ],
    
    setup: function(editor) {
      // زر حفظ منتج كويتي
      editor.ui.registry.addButton('saveKuwaitProduct', {
        text: '💾 حفظ KWD',
        tooltip: 'حفظ منتج من الكويت',
        onAction: function() {
          const content = editor.getContent();
          const blob = new Blob([`
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجات من متجر الكويت</title>
    <style>
        body {
            font-family: 'Cairo', Arial, sans-serif;
            direction: rtl;
            text-align: right;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .kuwait-product {
            background: #e8f5e8;
            border: 2px solid #28a745;
            border-radius: 8px;
            padding: 15px;
            margin: 12px 0;
            position: relative;
        }
        .kuwait-product:before {
            content: '🇰🇼';
            position: absolute;
            top: 5px;
            right: 5px;
            font-size: 16px;
        }
        .price-kwd {
            background: linear-gradient(45deg, #17a2b8, #20c997);
            color: white;
            padding: 6px 12px;
            border-radius: 15px;
            font-weight: bold;
            display: inline-block;
        }
        .kuwait-special {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 8px 12px;
            border-radius: 6px;
            color: #856404;
            font-weight: bold;
        }
        .header {
            background: linear-gradient(45deg, #17a2b8, #20c997);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🇰🇼 متجات من متجر الكويت</h1>
        </div>
        ${content}
        
        <hr style="margin: 30px 0; border: 2px solid #17a2b8;">
        <div style="text-align: center; color: #17a2b8; font-weight: bold;">
            <p>متجر الكويت - متجات من متجر الكويت</p>
            <p>https://sherow1982.github.io/Kuwait-matjar/</p>
            <p><small>${new Date().toLocaleDateString('ar-KW')}</small></p>
        </div>
    </div>
</body>
</html>
          `], { type: 'text/html;charset=utf-8' });
          
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `kuwait-matjar-${Date.now()}.html`;
          link.click();
          URL.revokeObjectURL(url);
          
          editor.notificationManager.open({
            text: 'تم حفظ متجات من الكويت! 🇰🇼',
            type: 'success',
            timeout: 3000
          });
        }
      });
      
      // زر إضافة الدينار الكويتي
      editor.ui.registry.addButton('addKWD', {
        text: 'KWD',
        tooltip: 'إضافة الدينار الكويتي',
        onAction: function() {
          editor.insertContent(' د.ك ');
        }
      });
      
      // زر علم الكويت
      editor.ui.registry.addButton('addKWFlag', {
        text: '🇰🇼',
        tooltip: 'علم دولة الكويت',
        onAction: function() {
          editor.insertContent('🇰🇼 ');
        }
      });
    }
  };
  
  tinymce.init(config);
}

// تهيئة تلقائية
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    loadTinyMCE().then(initKuwaitMatjarEditor).catch(console.error);
  });
} else {
  loadTinyMCE().then(initKuwaitMatjarEditor).catch(console.error);
}

// تصدير
window.KuwaitMatjarEditor = { loadTinyMCE, initKuwaitMatjarEditor };