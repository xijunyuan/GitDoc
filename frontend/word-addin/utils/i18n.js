/**
 * GitDoc I18N — 中英双语文本映射
 * ====================================
 * 提供所有 UI 文本的中英文版本。
 * 默认使用中文，保留关键英文术语。
 *
 * Usage:
 *   GitDoc.I18N.t("key")              → 中文文本
 *   GitDoc.I18N.t("status.ok")        → "已连接"
 */
var GitDoc = GitDoc || {};

(function(ns) {
    'use strict';

    var messages = {
        // 通用
        "app.title": "GitDoc - 文档版本管理",
        "app.subtitle": "Document Version Control",

        // 状态
        "status.connecting": "正在连接后端...",
        "status.connected": "已连接",
        "status.disconnected": "未连接",
        "status.error": "连接失败",

        // 面板标题
        "panel.history": "版本历史 (History)",
        "panel.diff": "差异对比 (Diff)",
        "panel.preview": "版本预览 (Preview)",
        "panel.rollback": "回滚确认 (Rollback Confirmation)",

        // 按钮
        "btn.refresh": "刷新列表 (Refresh)",
        "btn.save": "保存当前版本 (Save Version)",
        "btn.save.title": "保存当前版本",
        "btn.save.prompt": "请输入版本描述 (可选):",
        "btn.save.default": "[manual] 保存版本",
        "btn.preview": "预览 (Preview)",
        "btn.diff": "对比 (Diff)",
        "btn.rollback": "回滚到此版本 (Rollback)",
        "btn.back": "← 返回 (Back)",
        "btn.confirm": "确认回滚 (Confirm Rollback)",
        "btn.cancel": "取消 (Cancel)",

        // 差异统计
        "diff.stats": "统计",
        "diff.insertions": "新增",
        "diff.deletions": "删除",
        "diff.unchanged": "未变",
        "diff.comparing": "正在计算差异...",

        // 回滚
        "rollback.title": "⚠ 回滚到旧版本",
        "rollback.warning": "您即将把当前文档替换为以下版本：",
        "rollback.version": "版本",
        "rollback.date": "日期",
        "rollback.message": "提交信息",
        "rollback.backup": "当前文档将备份至:",
        "rollback.note": "回滚后请在 Word 中重新打开文档以查看变更。",
        "rollback.success": "回滚成功！",
        "rollback.failed": "回滚失败！",

        // 版本标签
        "version.current": "(HEAD, 当前版本)",
        "version.auto": "[auto]",
        "version.manual": "[manual]",

        // 错误
        "error.no_document": "未检测到打开的文档。请在 Word 中打开一个 .docx 文件。",
        "error.no_backend": "无法连接到 GitDoc 后端。请确认后端已启动。",
        "error.backend_init": "Git 仓库初始化失败。",
        "error.no_history": "暂无版本记录。保存文档后自动生成。",
        "error.diff_failed": "差异计算失败。",
        "error.rollback_failed": "回滚操作失败。",
        "error.git_not_found": "未检测到 Git。请安装 Git for Windows。",

        // 信息
        "info.loading": "加载中...",
        "info.no_changes": "文档内容未变更，无需提交。",
        "info.committed": "已提交为版本",
        "info.auto_commit": "[auto] 自动保存"
    };

    ns.I18N = {
        /**
         * Get a localized text string.
         * @param {string} key — Dot-separated key into the messages table.
         * @returns {string} The localized text, or the key itself if not found.
         */
        t: function(key) {
            return messages[key] || key;
        },

        /**
         * Format a template string with positional replacements.
         * @param {string} key — I18N key.
         * @param {...*} args — Replacement values for {0}, {1}, etc.
         * @returns {string}
         */
        fmt: function(key) {
            var text = messages[key] || key;
            var args = Array.prototype.slice.call(arguments, 1);
            return text.replace(/\{(\d+)\}/g, function(match, idx) {
                return typeof args[idx] !== 'undefined' ? String(args[idx]) : match;
            });
        },

        /**
         * Get all messages (for debugging / testing).
         */
        all: function() {
            return messages;
        }
    };

})(GitDoc);
