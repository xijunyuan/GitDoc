/**
 * GitDoc HistoryPanel — 版本历史时间轴
 * ======================================
 * Displays all versions in a vertical timeline with
 * preview, diff, and rollback action buttons.
 *
 * Usage:
 *   var panel = new GitDoc.HistoryPanel(document.getElementById("history-panel"), app);
 *   panel.show();
 */
var GitDoc = GitDoc || {};

(function(ns) {
    'use strict';

    function HistoryPanel(container, app) {
        this.container = container;
        this.app = app;
        this.commits = [];
        this.notes = {};       // {commit_hash: note_text}
        this.selectedForDiff = null; // hash selected as the "from" side for diff
    }

    HistoryPanel.prototype = {

        show: function() {
            var self = this;
            this.container.style.display = "block";
            this.container.innerHTML = '<div class="loading">' + ns.I18N.t("info.loading") + '</div>';

            // Fetch history and notes in parallel
            var path = this.app.currentDocxPath;
            Promise.all([
                this.app.api.getHistory(path),
                this.app.api.getNotes(path).catch(function() { return { notes: {} }; })
            ]).then(function(results) {
                self.commits = results[0].commits || [];
                self.notes = results[1].notes || {};
                self._render();
            }).catch(function(err) {
                self.container.innerHTML =
                    '<div class="error-box">' + ns.I18N.t("error.no_backend") + '<br>' +
                    '<small>' + err.message + '</small></div>';
            });
        },

        _render: function() {
            var self = this;
            var T = ns.I18N;

            if (this.commits.length === 0) {
                this.container.innerHTML =
                    '<div class="empty-state">' +
                    '<p>' + T.t("error.no_history") + '</p>' +
                    '</div>' +
                    this._renderToolbar();
                return;
            }

            var html = '<div class="history-timeline">';

            for (var i = 0; i < this.commits.length; i++) {
                var c = this.commits[i];
                var isFirst = (i === 0);
                var tag = c.version_tag || "";
                var shortHash = c.short_hash || c.hash.substring(0, 8);
                var ts = new Date(c.timestamp).toLocaleString("zh-CN");
                var isAuto = c.message.indexOf("[auto]") === 0;
                var badge = isAuto ? "auto" : "manual";
                var badgeClass = isAuto ? "badge-auto" : "badge-manual";
                var selectionHint = "";
                if (self.selectedForDiff && self.selectedForDiff === c.hash) {
                    selectionHint = ' <span class="diff-selected">← 对比基准 (Diff Base)</span>';
                }

                html += '<div class="timeline-item' + (isFirst ? " timeline-item-current" : "") + '">';
                html += '  <div class="timeline-dot"></div>';
                html += '  <div class="timeline-content">';
                html += '    <div class="timeline-header">';
                html += '      <span class="version-tag">' + tag + '</span>';
                if (isFirst) {
                    html += '      <span class="current-label">' + T.t("version.current") + '</span>';
                }
                html +=       selectionHint;
                html += '      <span class="badge ' + badgeClass + '">' + badge + '</span>';
                html += '    </div>';
                html += '    <div class="timeline-meta">';
                html += '      <span class="commit-hash" title="' + c.hash + '">' + shortHash + '</span>';
                html += '      <span class="commit-time">' + ts + '</span>';
                html += '    </div>';
                html += '    <div class="timeline-message">' + self._escapeHtml(c.message) + '</div>';
                // Note display / edit
                var note = self.notes[c.hash] || "";
                html += '    <div class="timeline-note" data-note-hash="' + c.hash + '">';
                if (note) {
                    html += '      <div class="note-display">'
                          + '<span class="note-icon">📝</span> '
                          + '<span class="note-text">' + self._escapeHtml(note) + '</span>'
                          + ' <button class="btn-note-edit" data-action="note-edit" data-hash="' + c.hash + '">✏️</button>'
                          + '</div>';
                } else {
                    html += '      <button class="btn-note-add" data-action="note-edit" data-hash="' + c.hash + '">+ 添加备注</button>';
                }
                html += '    </div>';
                html += '    <div class="timeline-actions">';
                html += '      <button class="btn-sm" data-action="preview" data-hash="' + c.hash + '">' + T.t("btn.preview") + '</button>';
                html += '      <button class="btn-sm" data-action="diff-select" data-hash="' + c.hash + '">' + T.t("btn.diff") + '</button>';
                html += '      <button class="btn-sm btn-danger" data-action="rollback" data-hash="' + c.hash + '" data-tag="' + tag + '">' + T.t("btn.rollback") + '</button>';
                html += '    </div>';
                html += '  </div>';
                html += '</div>';
            }

            html += '</div>';
            html += this._renderToolbar();

            this.container.innerHTML = html;
            this._bindEvents();
        },

        _renderToolbar: function() {
            var T = ns.I18N;
            return '' +
                '<div class="toolbar">' +
                '  <button class="btn" id="btn-refresh">' + T.t("btn.refresh") + '</button>' +
                '  <button class="btn btn-primary" id="btn-save-version">' + T.t("btn.save") + '</button>' +
                '</div>';
        },

        _bindEvents: function() {
            var self = this;
            var T = ns.I18N;

            // Refresh button
            var btnRefresh = document.getElementById("btn-refresh");
            if (btnRefresh) {
                btnRefresh.addEventListener("click", function() { self.show(); });
            }

            // Save Version button
            var btnSave = document.getElementById("btn-save-version");
            if (btnSave) {
                btnSave.addEventListener("click", function() {
                    var msg = prompt(T.t("btn.save.prompt"), T.t("btn.save.default"));
                    if (msg === null) return; // user cancelled
                    self.app.api.commit(self.app.currentDocxPath, msg)
                        .then(function(res) {
                            if (res.success) {
                                self.show();
                            } else {
                                alert(res.message);
                            }
                        })
                        .catch(function(err) {
                            alert(T.t("error.no_backend") + "\n" + err.message);
                        });
                });
            }

            // Note edit buttons
            var noteBtns = this.container.querySelectorAll("[data-action='note-edit']");
            for (var ni = 0; ni < noteBtns.length; ni++) {
                noteBtns[ni].addEventListener("click", function(e) {
                    e.stopPropagation();
                    var hash = this.getAttribute("data-hash");
                    self._editNote(hash);
                });
            }

            // Action buttons inside each timeline item
            var buttons = this.container.querySelectorAll("[data-action]");
            for (var i = 0; i < buttons.length; i++) {
                buttons[i].addEventListener("click", function(e) {
                    var action = this.getAttribute("data-action");
                    if (action === "note-edit") return; // handled above
                    var hash = this.getAttribute("data-hash");
                    var tag = this.getAttribute("data-tag");

                    switch (action) {
                        case "preview":
                            self.app.showPreviewView(hash);
                            break;

                        case "diff-select":
                            if (!self.selectedForDiff) {
                                self.selectedForDiff = hash;
                                self._render();
                                self._showDiffBanner(hash);
                            } else if (self.selectedForDiff === hash) {
                                self.selectedForDiff = null;
                                self._render();
                            } else {
                                var from = self.selectedForDiff;
                                self.selectedForDiff = null;
                                self.app.showDiffView(from, hash);
                            }
                            break;

                        case "rollback":
                            self.app.showRollbackView(hash, tag);
                            break;
                    }
                });
            }
        },

        /**
         * Replace the note display for a commit with an inline editor.
         */
        _editNote: function(hash) {
            var self = this;
            var noteDiv = this.container.querySelector("[data-note-hash='" + hash + "']");
            if (!noteDiv) return;

            var current = this.notes[hash] || "";

            noteDiv.innerHTML =
                '<textarea class="note-textarea" data-note-input="' + hash + '" '
                + 'placeholder="在此输入备注（说明修改了什么）..." '
                + 'style="width:100%;min-height:50px;padding:6px;border:1px solid #4a90d9;border-radius:4px;margin:4px 0;font-size:13px">'
                + self._escapeHtml(current) + '</textarea>'
                + '<div style="margin-top:4px">'
                + '<button class="btn-sm btn-primary" data-action="note-save" data-hash="' + hash + '">保存</button> '
                + '<button class="btn-sm" data-action="note-cancel" data-hash="' + hash + '">取消</button>'
                + '</div>';

            // Bind save/cancel
            var saveBtn = noteDiv.querySelector("[data-action='note-save']");
            var cancelBtn = noteDiv.querySelector("[data-action='note-cancel']");
            var textarea = noteDiv.querySelector("textarea");

            saveBtn.addEventListener("click", function() {
                var note = textarea.value.trim();
                self.app.api.saveNote(self.app.currentDocxPath, hash, note)
                    .then(function() {
                        self.notes[hash] = note;
                        self._render();
                    })
                    .catch(function(err) {
                        alert("保存备注失败: " + err.message);
                    });
            });

            cancelBtn.addEventListener("click", function() {
                self._render();
            });

            textarea.focus();
        },

        _showDiffBanner: function(hash) {
            // Show a banner prompting the user to select a second version
            var toolbar = this.container.querySelector(".toolbar");
            if (toolbar) {
                var banner = document.createElement("div");
                banner.className = "diff-banner";
                banner.innerHTML =
                    '<span>已选择对比基准: ' + hash.substring(0, 8) +
                    ' — 请点击另一个版本的"对比"按钮完成选择</span>' +
                    '<button class="btn-sm" id="btn-diff-cancel">取消</button>';
                toolbar.parentNode.insertBefore(banner, toolbar);

                document.getElementById("btn-diff-cancel").addEventListener("click", function() {
                    banner.remove();
                });
            }
        },

        _escapeHtml: function(text) {
            var div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }
    };

    ns.HistoryPanel = HistoryPanel;

})(GitDoc);
