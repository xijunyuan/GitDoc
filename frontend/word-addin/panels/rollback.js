/**
 * GitDoc RollbackPanel — 回滚确认对话框
 * =======================================
 * Modal confirmation dialog before performing a rollback.
 * Shows target version info and backup path disclaimer.
 *
 * Usage:
 *   var panel = new GitDoc.RollbackPanel(container, app);
 *   panel.show(commitHash, versionTag);
 */
var GitDoc = GitDoc || {};

(function(ns) {
    'use strict';

    function RollbackPanel(container, app) {
        this.container = container;
        this.app = app;
    }

    RollbackPanel.prototype = {

        show: function(commitHash, versionTag) {
            var self = this;
            var T = ns.I18N;

            // Find commit info from cached history
            var commit = null;
            var hp = this.app.historyPanel;
            if (hp && hp.commits) {
                for (var i = 0; i < hp.commits.length; i++) {
                    if (hp.commits[i].hash === commitHash) {
                        commit = hp.commits[i];
                        break;
                    }
                }
            }

            var shortHash = commitHash.substring(0, 8);
            var ts = commit ? new Date(commit.timestamp).toLocaleString("zh-CN") : "未知";
            var msg = commit ? commit.message : "未知";

            this.container.style.display = "flex"; // modal overlay uses flex to center

            var html = '';
            html += '<div class="modal-box">';
            html += '  <h2>' + T.t("rollback.title") + '</h2>';
            html += '  <p>' + T.t("rollback.warning") + '</p>';

            html += '  <div class="rollback-info-card">';
            html += '    <div class="info-row"><span class="info-label">' + T.t("rollback.version") + ':</span><span>' + (versionTag || shortHash) + '</span></div>';
            html += '    <div class="info-row"><span class="info-label">Hash:</span><span>' + shortHash + '</span></div>';
            html += '    <div class="info-row"><span class="info-label">' + T.t("rollback.date") + ':</span><span>' + ts + '</span></div>';
            html += '    <div class="info-row"><span class="info-label">' + T.t("rollback.message") + ':</span><span>' + self._escapeHtml(msg) + '</span></div>';
            html += '  </div>';

            html += '  <div class="rollback-backup-info">';
            html += '    <p>' + T.t("rollback.backup") + '</p>';
            html += '    <code>.gitdoc/backups/pre_rollback_*.docx</code>';
            html += '  </div>';

            html += '  <p class="rollback-note">' + T.t("rollback.note") + '</p>';

            html += '  <div class="modal-actions">';
            html += '    <button class="btn" id="btn-rollback-cancel">' + T.t("btn.cancel") + '</button>';
            html += '    <button class="btn btn-danger" id="btn-rollback-confirm">' + T.t("btn.confirm") + '</button>';
            html += '  </div>';
            html += '</div>';

            this.container.innerHTML = html;

            // Bind events
            document.getElementById("btn-rollback-cancel").addEventListener("click", function() {
                self.container.style.display = "none";
                self.app.showHistoryView();
            });

            document.getElementById("btn-rollback-confirm").addEventListener("click", function() {
                self._executeRollback(commitHash);
            });
        },

        _executeRollback: function(commitHash) {
            var self = this;
            var T = ns.I18N;

            // Show loading state
            var confirmBtn = document.getElementById("btn-rollback-confirm");
            var cancelBtn = document.getElementById("btn-rollback-cancel");
            if (confirmBtn) confirmBtn.disabled = true;
            if (cancelBtn) cancelBtn.disabled = true;

            this.app.api.rollback(commitHash, this.app.currentDocxPath)
                .then(function(result) {
                    if (result.success) {
                        alert(T.t("rollback.success") + "\n\n" + result.message);
                        self.container.style.display = "none";
                        self.app.showHistoryView();
                    } else {
                        alert(T.t("rollback.failed") + "\n" + result.message);
                        if (confirmBtn) confirmBtn.disabled = false;
                        if (cancelBtn) cancelBtn.disabled = false;
                    }
                })
                .catch(function(err) {
                    alert(T.t("error.rollback_failed") + "\n" + err.message);
                    if (confirmBtn) confirmBtn.disabled = false;
                    if (cancelBtn) cancelBtn.disabled = false;
                });
        },

        _escapeHtml: function(text) {
            var div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }
    };

    ns.RollbackPanel = RollbackPanel;

})(GitDoc);
