/**
 * GitDoc Word Add-in — Main Entry Point
 * ======================================
 * GitDoc.App is the core orchestrator that:
 * - Initializes Office.js and connects to the Python backend
 * - Manages view routing between panels (history, diff, preview, rollback)
 * - Handles auto-start of the Python backend process
 * - Binds Word document events (save, close)
 *
 * All modules use the global "GitDoc" namespace (IIFE pattern).
 */
var GitDoc = GitDoc || {};

(function(ns) {
    'use strict';

    // ===================== App Constructor =====================

    function App() {
        this.api = new ns.ApiClient("");
        this.bus = new ns.EventBus();
        this.currentDocxPath = null;
        this.currentView = "history";

        // Panel instances (created after DOM ready)
        this.historyPanel = null;
        this.diffPanel = null;
        this.rollbackPanel = null;
        this.previewPanel = null;
    }

    App.prototype = {

        // ===================== Initialization =====================

        /**
         * Initialize the plugin. Called once Office.js is ready.
         */
        initialize: function() {
            var self = this;
            var T = ns.I18N;

            console.log("[GitDoc] Initializing...");

            // Create panel instances
            this.historyPanel = new ns.HistoryPanel(
                document.getElementById("history-panel"), this
            );
            this.diffPanel = new ns.DiffPanel(
                document.getElementById("diff-panel"), this
            );
            this.rollbackPanel = new ns.RollbackPanel(
                document.getElementById("rollback-panel"), this
            );
            this.previewPanel = new ns.PreviewPanel(
                document.getElementById("preview-panel"), this
            );

            // Set the global reference for ribbon callbacks
            window.gitdocApp = this;

            // Get the active document's path
            this._getDocumentPath()
                .then(function(docxPath) {
                    // Hide loading spinner
                    var spinner = document.getElementById("loading-spinner");
                    if (spinner) spinner.style.display = "none";

                    if (!docxPath || self._isMockPath(docxPath)) {
                        // Could not auto-detect — show manual setup
                        self._showSetupPanel();
                        return;
                    }
                    self.currentDocxPath = docxPath;
                    console.log("[GitDoc] Document path:", docxPath);
                    return self._connectAndInit();
                })
                .catch(function(err) {
                    console.error("[GitDoc] Initialization failed:", err);
                    self._showSetupPanel();
                });

            // Register Office.js event handlers
            this._bindOfficeEvents();
        },

        /**
         * Get the full path of the currently active Word document.
         * Uses Office.js getFilePropertiesAsync API.
         * @returns {Promise<string|null>}
         */
        _getDocumentPath: function() {
            return new Promise(function(resolve) {
                try {
                    if (typeof Office === "undefined" || !Office.context) {
                        // Not running inside Office — try fallback
                        console.warn("[GitDoc] Office.js not available, using mock path");
                        resolve(_getMockDocxPath());
                        return;
                    }

                    Office.context.document.getFilePropertiesAsync(function(result) {
                        if (result.status === Office.AsyncResultStatus.Succeeded) {
                            // Note: Office.js does NOT expose the full filesystem path
                            // for security reasons. We use the URL as a proxy.
                            var url = result.value.url || "";
                            console.log("[GitDoc] Document URL:", url);

                            // Convert file:// URL to filesystem path on Windows
                            var path = _urlToPath(url) || _getMockDocxPath();
                            resolve(path);
                        } else {
                            console.warn("[GitDoc] getFilePropertiesAsync failed, using mock path");
                            resolve(_getMockDocxPath());
                        }
                    });
                } catch (e) {
                    console.warn("[GitDoc] Office.js error, using mock path:", e.message);
                    resolve(_getMockDocxPath());
                }
            });
        },

        /**
         * Check if path is a mock/fallback that needs user override.
         */
        _isMockPath: function(path) {
            return !path || path.indexOf("Public\\Documents") !== -1;
        },

        /**
         * Show the manual document-path setup panel.
         */
        _showSetupPanel: function() {
            this._hideAllPanels();
            var panel = document.getElementById("setup-panel");
            if (panel) panel.style.display = "block";
            this.currentView = "setup";

            var self = this;
            var btn = document.getElementById("btn-set-docx");
            if (btn) {
                btn.onclick = function() {
                    var input = document.getElementById("docx-path-input");
                    var path = input ? input.value.trim() : "";
                    if (!path) {
                        alert("请输入 .docx 文件路径");
                        return;
                    }
                    self.currentDocxPath = path;
                    var panel2 = document.getElementById("setup-panel");
                    if (panel2) panel2.style.display = "none";
                    var spinner = document.getElementById("loading-spinner");
                    if (spinner) spinner.style.display = "flex";
                    self._connectAndInit().then(function() {
                        if (spinner) spinner.style.display = "none";
                    }).catch(function(err) {
                        if (spinner) spinner.style.display = "none";
                        self._showError(ns.I18N.t("error.no_backend") + " — " + err.message);
                    });
                };
            }
        },

        /**
         * Connect to backend and initialize the document repo.
         */
        _connectAndInit: function() {
            var self = this;
            return this._connectBackend()
                .then(function() {
                    return self.api.initRepo(self.currentDocxPath);
                })
                .then(function() {
                    self._hideError();
                    self.showHistoryView();
                });
        },

        /**
         * Connect to the Python backend with retries.
         * @returns {Promise<void>}
         */
        _connectBackend: function() {
            var self = this;
            var maxRetries = 10;
            var retryDelay = 1000; // 1 second between retries

            function tryConnect(attempt) {
                return self.api.getStatus()
                    .then(function(status) {
                        if (status.status === "ok") {
                            console.log("[GitDoc] Backend connected:", status);
                            var statusEl = document.getElementById("connection-status");
                            if (statusEl) {
                                statusEl.textContent = ns.I18N.t("status.connected");
                                statusEl.className = "status-ok";
                            }

                            // Warn if Git is not available
                            if (!status.git_version) {
                                self._showWarning(ns.I18N.t("error.git_not_found"));
                            }
                            return;
                        }
                        throw new Error("Backend not ready");
                    })
                    .catch(function(err) {
                        if (attempt < maxRetries) {
                            console.log("[GitDoc] Retry " + attempt + "/" + maxRetries + "...");
                            return _delay(retryDelay).then(function() {
                                return tryConnect(attempt + 1);
                            });
                        }
                        throw err;
                    });
            }

            return tryConnect(1);
        },

        /**
         * Register Office.js event handlers (document save, close).
         */
        _bindOfficeEvents: function() {
            var self = this;

            try {
                if (typeof Office === "undefined" || !Office.context) {
                    return;
                }

                // Document saved event — refresh history
                Office.context.document.addHandlerAsync(
                    Office.EventType.DocumentSelectionChanged,
                    function() {
                        // This fires frequently; we rely on the file watcher
                        // for auto-commits. Could debounce a history refresh.
                    }
                );
            } catch (e) {
                console.warn("[GitDoc] Could not bind Office events:", e.message);
            }

            // On window unload, send shutdown to backend
            window.addEventListener("beforeunload", function() {
                self._shutdownBackend();
            });
        },

        /**
         * Graceful shutdown: send shutdown request to backend.
         */
        _shutdownBackend: function() {
            try {
                // Use synchronous XHR for beforeunload (fetch may not complete)
                var xhr = new XMLHttpRequest();
                xhr.open("POST", "/api/shutdown", false);
                xhr.setRequestHeader("Content-Type", "application/json");
                xhr.send("{}");
            } catch (e) {
                // Backend may already be down — ignore
            }
        },

        // ===================== View Routing =====================

        /**
         * Show the version history timeline (default view).
         */
        showHistoryView: function() {
            this._hideAllPanels();
            this.historyPanel.show();
            this.currentView = "history";
            this._updateTabBar("history");
        },

        /**
         * Show diff between two versions.
         * @param {string} fromHash — Older version hash.
         * @param {string} toHash — Newer version hash.
         */
        showDiffView: function(fromHash, toHash) {
            this._hideAllPanels();
            this.diffPanel.show(fromHash, toHash);
            this.currentView = "diff";
            this._updateTabBar("diff");
        },

        /**
         * Show rollback confirmation dialog.
         * @param {string} commitHash — Target version hash.
         * @param {string} versionTag — Display label (e.g. "v3").
         */
        showRollbackView: function(commitHash, versionTag) {
            this._hideAllPanels();
            this.rollbackPanel.show(commitHash, versionTag);
            this.currentView = "rollback";
        },

        /**
         * Show text preview of a specific version.
         * @param {string} commitHash — Version hash.
         */
        showPreviewView: function(commitHash) {
            this._hideAllPanels();
            this.previewPanel.show(commitHash);
            this.currentView = "preview";
            this._updateTabBar("preview");
        },

        /**
         * Hide all panel divs.
         */
        _hideAllPanels: function() {
            var panelIds = ["setup-panel", "history-panel", "diff-panel", "rollback-panel", "preview-panel"];
            for (var i = 0; i < panelIds.length; i++) {
                var el = document.getElementById(panelIds[i]);
                if (el) el.style.display = "none";
            }
        },

        /**
         * Update the tab bar active indicator.
         */
        _updateTabBar: function(view) {
            var tabs = document.querySelectorAll(".tab-bar .tab");
            for (var i = 0; i < tabs.length; i++) {
                var tabView = tabs[i].getAttribute("data-view");
                if (tabView === view) {
                    tabs[i].classList.add("active");
                } else {
                    tabs[i].classList.remove("active");
                }
            }
        },

        // ===================== UI Helpers =====================

        _showError: function(message) {
            var el = document.getElementById("error-message");
            if (el) {
                el.textContent = message;
                el.style.display = "block";
            }
        },

        _showWarning: function(message) {
            console.warn("[GitDoc]", message);
            var el = document.getElementById("warning-message");
            if (el) {
                el.textContent = message;
                el.style.display = "block";
            }
        },

        _hideError: function() {
            var el = document.getElementById("error-message");
            if (el) el.style.display = "none";
        }
    };

    // ===================== Helpers =====================

    /**
     * Convert a file:// URL to a Windows filesystem path.
     */
    function _urlToPath(url) {
        if (!url) return null;
        // Handle file:///C:/Users/... format
        var match = url.match(/^file:\/\/\/(.*)$/);
        if (match) {
            return decodeURIComponent(match[1].replace(/\//g, "\\"));
        }
        return null;
    }

    /**
     * Get a mock document path for development/testing outside Word.
     */
    function _getMockDocxPath() {
        // Try environment variable first
        if (typeof window !== "undefined" && window.GITDOC_TEST_PATH) {
            return window.GITDOC_TEST_PATH;
        }
        // Fallback: look for .docx files in the user's Documents folder
        return "C:\\Users\\Public\\Documents\\test.docx";
    }

    /**
     * Return a promise that resolves after ms milliseconds.
     */
    function _delay(ms) {
        return new Promise(function(resolve) {
            setTimeout(resolve, ms);
        });
    }

    // ===================== Boot =====================

    /**
     * Initialize the app when the DOM is ready.
     * If Office.js is present, wait for it; otherwise start immediately.
     */
    function boot() {
        var app = new App();

        // Store app reference globally for ribbon callbacks
        window.gitdocPlugin = app;

        if (typeof Office !== "undefined" && Office.onReady) {
            Office.onReady(function(info) {
                console.log("[GitDoc] Office.js ready:", info.host);
                app.initialize();
            });
        } else {
            // Running outside Word (development mode)
            console.log("[GitDoc] Running in standalone mode (no Office.js)");
            document.addEventListener("DOMContentLoaded", function() {
                app.initialize();
            });
        }
    }

    // Export App constructor
    ns.App = App;

    // Auto-boot when script loads (DOM may or may not be ready)
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }

})(GitDoc);
