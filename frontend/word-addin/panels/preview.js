/**
 * GitDoc PreviewPanel — 版本文本预览
 * =====================================
 * Displays a read-only plain-text view of a specific version's content.
 * Includes a "Rollback to this version" button at the bottom.
 *
 * Usage:
 *   var panel = new GitDoc.PreviewPanel(container, app);
 *   panel.show(commitHash);
 */
var GitDoc = GitDoc || {};

(function(ns) {
    'use strict';

    function PreviewPanel(container, app) {
        this.container = container;
        this.app = app;
        this.currentHash = null;
    }

    PreviewPanel.prototype = {

        show: function(commitHash) {
            var self = this;
            var T = ns.I18N;

            this.currentHash = commitHash;
            this.container.style.display = "block";
            this.container.innerHTML = '<div class="loading">' + T.t("info.loading") + '</div>';

            this.app.api.preview(commitHash, this.app.currentDocxPath)
                .then(function(result) {
                    self._render(commitHash, result);
                })
                .catch(function(err) {
                    self.container.innerHTML =
                        '<div class="error-box">加载预览失败: ' + err.message + '</div>';
                });
        },

        _render: function(commitHash, result) {
            var T = ns.I18N;
            var shortHash = commitHash.substring(0, 8);
            var blocks = result.text ? result.text.split("\n\n") : [];

            var html = '';

            // Header
            html += '<div class="preview-header">';
            html += '  <button class="btn btn-back" id="btn-preview-back">' + T.t("btn.back") + '</button>';
            html += '  <h2>' + T.t("panel.preview") + '</h2>';
            html += '  <div class="preview-meta">';
            html += '    <span>版本: ' + shortHash + '</span>';
            html += '    <span>段落数: ' + result.block_count + '</span>';
            html += '  </div>';
            html += '</div>';

            // Content (read-only text)
            html += '<div class="preview-content">';
            for (var i = 0; i < blocks.length; i++) {
                var blockText = blocks[i].trim();
                if (!blockText) continue;
                html += '<div class="preview-block">';
                html += '  <div class="preview-block-num">' + (i + 1) + '</div>';
                html += '  <div class="preview-block-text">' + this._escapeHtml(blockText) + '</div>';
                html += '</div>';
            }
            html += '</div>';

            // Action bar
            html += '<div class="preview-actions">';
            html += '  <button class="btn btn-danger" id="btn-preview-rollback">' +
                    T.t("btn.rollback") + '</button>';
            html += '</div>';

            this.container.innerHTML = html;

            // Bind events
            var self = this;
            document.getElementById("btn-preview-back").addEventListener("click", function() {
                self.app.showHistoryView();
            });

            document.getElementById("btn-preview-rollback").addEventListener("click", function() {
                self.app.showRollbackView(commitHash, shortHash);
            });
        },

        _escapeHtml: function(text) {
            var div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }
    };

    ns.PreviewPanel = PreviewPanel;

})(GitDoc);
