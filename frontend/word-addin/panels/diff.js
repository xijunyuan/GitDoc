/**
 * GitDoc DiffPanel — 差异对比视图
 * ==================================
 * Displays a word-level diff between two document versions
 * with green highlights for insertions and red for deletions.
 *
 * Usage:
 *   var panel = new GitDoc.DiffPanel(container, app);
 *   panel.show(fromHash, toHash);
 */
var GitDoc = GitDoc || {};

(function(ns) {
    'use strict';

    function DiffPanel(container, app) {
        this.container = container;
        this.app = app;
    }

    DiffPanel.prototype = {

        show: function(fromHash, toHash) {
            var self = this;
            var T = ns.I18N;

            this.container.style.display = "block";
            this.container.innerHTML = '<div class="loading">' + T.t("diff.comparing") + '</div>';

            this.app.api.getDiff(fromHash, toHash, this.app.currentDocxPath)
                .then(function(result) {
                    self._render(fromHash, toHash, result);
                })
                .catch(function(err) {
                    self.container.innerHTML =
                        '<div class="error-box">' + T.t("error.diff_failed") + '<br>' +
                        '<small>' + err.message + '</small></div>';
                });
        },

        _render: function(fromHash, toHash, result) {
            var T = ns.I18N;
            var stats = result.stats;

            var html = '';

            // Header
            html += '<div class="diff-header">';
            html += '  <button class="btn btn-back" id="btn-diff-back">' + T.t("btn.back") + '</button>';
            html += '  <h2>' + T.t("panel.diff") + '</h2>';
            html += '  <div class="diff-version-labels">';
            html += '    <span class="diff-from">← ' + fromHash.substring(0, 8) + '</span>';
            html += '    <span class="diff-arrow">vs</span>';
            html += '    <span class="diff-to">' + toHash.substring(0, 8) + ' →</span>';
            html += '  </div>';
            html += '</div>';

            // Stats bar
            html += '<div class="diff-stats-bar">';
            html += '  <span class="stat-label">' + T.t("diff.stats") + ': </span>';
            html += '  <span class="stat-insert">+' + stats.insertions + ' ' + T.t("diff.insertions") + '</span>';
            html += '  <span class="stat-delete">-' + stats.deletions + ' ' + T.t("diff.deletions") + '</span>';
            html += '  <span class="stat-equal">=' + stats.equal + ' ' + T.t("diff.unchanged") + '</span>';
            html += '</div>';

            // Diff content
            html += '<div class="diff-content">';
            var blocks = result.blocks || [];
            for (var i = 0; i < blocks.length; i++) {
                var block = blocks[i];
                html += '<div class="diff-block">';
                html += '  <div class="diff-block-label">' +
                        '段落 ' + (block.block_index + 1) + ' (' + block.block_type + ')' +
                        '</div>';
                html += '  <div class="diff-block-text">';
                var segments = block.segments || [];
                for (var j = 0; j < segments.length; j++) {
                    var seg = segments[j];
                    html += '<span class="diff-' + seg.operation + '">' +
                            this._escapeHtml(seg.text) +
                            '</span>';
                }
                html += '  </div>';
                html += '</div>';
            }
            html += '</div>';

            this.container.innerHTML = html;

            // Bind back button
            var self = this;
            document.getElementById("btn-diff-back").addEventListener("click", function() {
                self.app.showHistoryView();
            });
        },

        _escapeHtml: function(text) {
            var div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }
    };

    ns.DiffPanel = DiffPanel;

})(GitDoc);
