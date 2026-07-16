/**
 * GitDoc API Client
 * ==================
 * HTTP client for communicating with the GitDoc Python backend.
 * All API calls return Promises.
 *
 * Usage:
 *   var api = new GitDoc.ApiClient("http://127.0.0.1:18521");
 *   api.getStatus().then(function(status) { ... });
 */
var GitDoc = GitDoc || {};

(function(ns) {
    'use strict';

    /**
     * @constructor
     * @param {string} baseUrl — Backend URL, defaults to localhost:18521.
     */
    function ApiClient(baseUrl) {
        this.baseUrl = baseUrl || "";
    }

    ApiClient.prototype = {

        /**
         * Internal fetch wrapper.
         * @param {string} endpoint — API path (e.g. "/api/status").
         * @param {object} [options] — Fetch options (method, body, etc.).
         * @returns {Promise<object>} Parsed JSON response.
         */
        _fetch: function(endpoint, options) {
            options = options || {};
            var url = this.baseUrl + endpoint;
            var config = {
                method: options.method || "GET",
                headers: Object.assign({
                    "Content-Type": "application/json"
                }, options.headers || {})
            };

            if (options.body) {
                config.body = JSON.stringify(options.body);
            }

            return fetch(url, config).then(function(response) {
                if (!response.ok) {
                    return response.text().then(function(text) {
                        throw new Error("API error " + response.status + ": " + text);
                    });
                }
                return response.json();
            });
        },

        // ---- Endpoints ----

        /**
         * Health check / connection test.
         * GET /api/status
         */
        getStatus: function() {
            return this._fetch("/api/status");
        },

        /**
         * Initialize Git repository for a document and start file watching.
         * POST /api/init
         * @param {string} docxPath — Full path to the .docx file.
         * @param {string} [author] — Author name.
         * @param {string} [email] — Author email.
         */
        initRepo: function(docxPath, author, email) {
            return this._fetch("/api/init", {
                method: "POST",
                body: {
                    docx_path: docxPath,
                    author: author || "GitDoc User",
                    email: email || "user@gitdoc.local"
                }
            });
        },

        /**
         * Create a manual commit (Save Version button).
         * POST /api/commit
         * @param {string} docxPath — Full path to the .docx file.
         * @param {string} [message] — Commit message.
         * @param {string} [author] — Author name.
         */
        commit: function(docxPath, message, author) {
            return this._fetch("/api/commit", {
                method: "POST",
                body: {
                    docx_path: docxPath,
                    message: message || "[manual] 保存版本",
                    author: author || "GitDoc User"
                }
            });
        },

        /**
         * Get version history for a document.
         * GET /api/history?docx_path=...
         * @param {string} docxPath — Full path to the .docx file.
         */
        getHistory: function(docxPath) {
            return this._fetch("/api/history?docx_path=" + encodeURIComponent(docxPath));
        },

        /**
         * Compute diff between two versions.
         * GET /api/diff?from_hash=...&to_hash=...&docx_path=...
         * @param {string} fromHash — Old version commit hash.
         * @param {string} toHash — New version commit hash.
         * @param {string} docxPath — Full path to the .docx file.
         */
        getDiff: function(fromHash, toHash, docxPath) {
            var params = "from_hash=" + encodeURIComponent(fromHash) +
                        "&to_hash=" + encodeURIComponent(toHash) +
                        "&docx_path=" + encodeURIComponent(docxPath);
            return this._fetch("/api/diff?" + params);
        },

        /**
         * Rollback document to a specific version.
         * POST /api/rollback
         * @param {string} commitHash — Target commit hash.
         * @param {string} docxPath — Full path to the .docx file.
         */
        rollback: function(commitHash, docxPath, saveAsNew) {
            return this._fetch("/api/rollback", {
                method: "POST",
                body: {
                    commit_hash: commitHash,
                    docx_path: docxPath,
                    save_as_new: saveAsNew || false
                }
            });
        },

        /**
         * Get plain text preview of a specific version.
         * GET /api/preview?commit_hash=...&docx_path=...
         * @param {string} commitHash — Commit hash.
         * @param {string} docxPath — Full path to the .docx file.
         */
        preview: function(commitHash, docxPath) {
            var params = "commit_hash=" + encodeURIComponent(commitHash) +
                        "&docx_path=" + encodeURIComponent(docxPath);
            return this._fetch("/api/preview?" + params);
        },

        /**
         * Shut down the backend gracefully.
         * POST /api/shutdown
         */
        shutdown: function() {
            return this._fetch("/api/shutdown", { method: "POST" });
        },

        /**
         * Get all notes for a document.
         * GET /api/notes?docx_path=...
         */
        getNotes: function(docxPath) {
            return this._fetch("/api/notes?docx_path=" + encodeURIComponent(docxPath));
        },

        /**
         * Save a note for a specific commit.
         * POST /api/notes
         */
        saveNote: function(docxPath, commitHash, note) {
            return this._fetch("/api/notes", {
                method: "POST",
                body: {
                    docx_path: docxPath,
                    commit_hash: commitHash,
                    note: note
                }
            });
        }
    };

    ns.ApiClient = ApiClient;

})(GitDoc);
