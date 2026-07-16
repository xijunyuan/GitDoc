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

        _executeRollback: function(commitHash, saveAsNew) {
            var self = this;
            var T = ns.I18N;
            saveAsNew = saveAsNew || false;

            console.log("[GitDoc] Rollback started, hash=" + commitHash +
                       ", saveAsNew=" + saveAsNew + ", path=" + this.app.currentDocxPath);

            var modalBox = this.container.querySelector(".modal-box");
            var oldFooter = modalBox ? modalBox.querySelector(".modal-actions") : null;
            if (oldFooter) {
                oldFooter.innerHTML = '<p style="text-align:center;color:#666;">⏳ 正在回滚，请稍候...</p>';
            }

            this.app.api.rollback(commitHash, this.app.currentDocxPath, saveAsNew)
                .then(function(result) {
                    console.log("[GitDoc] Rollback response:", result);
                    if (!oldFooter) return;

                    if (result.locked_by_word) {
                        // Word has the file locked — show choice dialog
                        oldFooter.innerHTML =
                            '<div style="background:#fff3e0;padding:12px;border-radius:6px;margin-top:8px">' +
                            '<p style="color:#e65100;font-weight:bold;margin-bottom:8px">⚠ 文档正被 Word 打开</p>' +
                            '<p style="color:#333;font-size:13px;margin-bottom:12px">' +
                            self._escapeHtml(result.message) + '</p>' +
                            '<button class="btn btn-danger" id="btn-save-as-new" ' +
                            'style="margin-right:8px">📄 另存为新文件</button>' +
                            '<button class="btn" id="btn-retry-direct">🔄 关闭文档后重试覆盖</button></div>';

                        document.getElementById("btn-save-as-new").addEventListener("click", function() {
                            self._executeRollback(commitHash, true);
                        });
                        document.getElementById("btn-retry-direct").addEventListener("click", function() {
                            self._executeRollback(commitHash, false);
                        });
                    } else if (result.success) {
                        oldFooter.innerHTML =
                            '<div style="background:#e8f5e9;padding:12px;border-radius:6px;margin-top:8px">' +
                            '<p style="color:#2e7d32;font-weight:bold">✅ 回滚成功</p>' +
                            '<p style="color:#333;white-space:pre-wrap;font-size:13px">' +
                            self._escapeHtml(result.message) + '</p>' +
                            '<button class="btn" onclick="location.reload()" ' +
                            'style="margin-top:8px">刷新页面</button></div>';
                    } else {
                        oldFooter.innerHTML =
                            '<div style="background:#ffebee;padding:12px;border-radius:6px;margin-top:8px">' +
                            '<p style="color:#c62828;font-weight:bold">❌ 回滚失败</p>' +
                            '<p style="color:#333;white-space:pre-wrap;font-size:13px">' +
                            self._escapeHtml(result.message) + '</p>' +
                            '<button class="btn" id="btn-retry-rollback" style="margin-top:8px">重试</button></div>';
                        document.getElementById("btn-retry-rollback").addEventListener("click", function() {
                            self._executeRollback(commitHash);
                        });
                    }
                })
                .catch(function(err) {
                    console.error("[GitDoc] Rollback error:", err);
                    if (oldFooter) {
                        oldFooter.innerHTML =
                            '<div style="background:#ffebee;padding:12px;border-radius:6px;margin-top:8px">' +
                            '<p style="color:#c62828;font-weight:bold">❌ 网络错误</p>' +
                            '<p style="color:#333;font-size:13px">' + self._escapeHtml(err.message) + '</p>' +
                            '<button class="btn" id="btn-retry-rollback" style="margin-top:8px">重试</button></div>';
                        document.getElementById("btn-retry-rollback").addEventListener("click", function() {
                            self._executeRollback(commitHash);
                        });
                    }
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
