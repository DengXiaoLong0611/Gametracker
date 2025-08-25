// 全局JavaScript功能
class PortfolioApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupBackToTop();
        this.setupLazyLoading();
        this.setupImageModal();
        this.setupSmoothScroll();
        this.setupSearchFeatures();
        this.setupLoadingStates();
    }

    // 回到顶部功能
    setupBackToTop() {
        const backToTopBtn = document.getElementById('btn-back-to-top');
        if (!backToTopBtn) return;

        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        });

        backToTopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // 图片懒加载
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        const src = img.getAttribute('data-src');
                        if (src) {
                            img.setAttribute('src', src);
                            img.removeAttribute('data-src');
                            img.classList.add('fade-in');
                        }
                        observer.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    // 图片模态框
    setupImageModal() {
        // 创建模态框HTML
        if (!document.getElementById('imageModal')) {
            const modalHTML = `
                <div class="modal fade" id="imageModal" tabindex="-1">
                    <div class="modal-dialog modal-xl modal-dialog-centered">
                        <div class="modal-content bg-transparent border-0">
                            <div class="modal-header border-0">
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body text-center p-0">
                                <img id="modalImage" src="" alt="" class="img-fluid rounded">
                                <div class="mt-3 text-white">
                                    <h5 id="modalTitle"></h5>
                                    <p id="modalDescription" class="small"></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }

        // 绑定点击事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('work-image') || e.target.closest('.work-image-wrapper')) {
                e.preventDefault();
                const img = e.target.closest('.work-card')?.querySelector('.work-image');
                const title = e.target.closest('.work-card')?.querySelector('.card-title')?.textContent;
                const description = e.target.closest('.work-card')?.querySelector('.card-text')?.textContent;
                
                if (img) {
                    this.showImageModal(img.src, title || '', description || '');
                }
            }
        });
    }

    showImageModal(src, title, description) {
        const modal = document.getElementById('imageModal');
        const modalImage = document.getElementById('modalImage');
        const modalTitle = document.getElementById('modalTitle');
        const modalDescription = document.getElementById('modalDescription');
        
        modalImage.src = src;
        modalTitle.textContent = title;
        modalDescription.textContent = description;
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    // 平滑滚动
    setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // 搜索功能
    setupSearchFeatures() {
        const searchInput = document.getElementById('searchInput');
        if (!searchInput) return;

        let searchTimeout;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });
    }

    async performSearch(query) {
        if (query.length < 2) {
            this.clearSearch();
            return;
        }

        try {
            const response = await fetch(`/api/works?search=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.displaySearchResults(data.works);
        } catch (error) {
            console.error('搜索失败:', error);
            this.showMessage('搜索失败，请稍后重试', 'error');
        }
    }

    displaySearchResults(works) {
        const container = document.getElementById('worksContainer');
        if (!container) return;

        if (works.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">没有找到相关作品</h4>
                    <p class="text-muted">请尝试其他关键词</p>
                </div>
            `;
            return;
        }

        container.innerHTML = works.map(work => this.renderWorkCard(work)).join('');
    }

    renderWorkCard(work) {
        const thumbnailSrc = work.thumbnail_path || '/static/images/placeholder.jpg';
        const workTypeIcon = this.getWorkTypeIcon(work.work_type);
        
        return `
            <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
                <div class="work-card card h-100 border-0 shadow-hover">
                    <div class="work-image-wrapper position-relative overflow-hidden">
                        <img src="${thumbnailSrc}" class="work-image card-img-top" alt="${work.title}">
                        <div class="work-overlay position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center">
                            <div class="text-center text-white">
                                <a href="/work/${work.id}" class="btn btn-primary btn-sm mb-2">
                                    <i class="fas fa-eye me-1"></i>查看详情
                                </a>
                                <div class="work-stats d-flex justify-content-center gap-3 small">
                                    <span><i class="fas fa-eye me-1"></i>${work.view_count}</span>
                                    <span><i class="fas fa-heart me-1"></i>${work.like_count}</span>
                                </div>
                            </div>
                        </div>
                        <div class="position-absolute top-0 end-0 p-2">
                            <span class="badge bg-primary">${workTypeIcon}</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <h6 class="card-title fw-bold mb-2">${work.title}</h6>
                        ${work.description ? `<p class="card-text text-muted small">${work.description.substring(0, 100)}...</p>` : ''}
                        <div class="d-flex align-items-center justify-content-between small text-muted">
                            <span>
                                <i class="fas fa-calendar me-1"></i>
                                ${new Date(work.created_at).toLocaleDateString('zh-CN')}
                            </span>
                            ${work.is_featured ? '<span class="badge bg-success">精选</span>' : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getWorkTypeIcon(workType) {
        const icons = {
            'photo': '📸 摄影',
            'text': '📝 文字', 
            'video': '🎬 视频',
            'audio': '🎵 音频',
            'document': '📄 文档',
            'other': '🎨 其他'
        };
        return icons[workType] || icons['other'];
    }

    clearSearch() {
        // 清除搜索结果，恢复原始内容
        window.location.reload();
    }

    // 加载状态管理
    setupLoadingStates() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM') {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    this.setLoading(submitBtn, true);
                }
            }
        });
    }

    setLoading(element, isLoading) {
        if (isLoading) {
            element.disabled = true;
            const originalText = element.textContent;
            element.setAttribute('data-original-text', originalText);
            element.innerHTML = '<span class="loading me-2"></span>加载中...';
        } else {
            element.disabled = false;
            const originalText = element.getAttribute('data-original-text');
            element.textContent = originalText || element.textContent;
            element.removeAttribute('data-original-text');
        }
    }

    // 消息提示
    showMessage(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const alertHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
                 style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', alertHTML);

        // 自动消失
        setTimeout(() => {
            const alert = document.querySelector('.alert');
            if (alert) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    // API 请求封装
    async apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API请求失败:', error);
            this.showMessage('请求失败，请稍后重试', 'error');
            throw error;
        }
    }

    // 工具方法：格式化日期
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    // 工具方法：格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 工具方法：防抖
    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    // 工具方法：节流
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', function() {
    const app = new PortfolioApp();
    
    // 全局暴露app实例，方便调试和其他脚本使用
    window.portfolioApp = app;
    
    // 添加页面切换效果
    document.body.classList.add('fade-in-up');
    
    console.log('🎨 Portfolio Showcase 加载完成');
});

// Service Worker 注册 (PWA支持)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('SW registered: ', registration);
            })
            .catch(function(registrationError) {
                console.log('SW registration failed: ', registrationError);
            });
    });
}