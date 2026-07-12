/**
 * GitDoc EventBus — 简单发布/订阅事件总线
 * ===========================================
 * 用于前端各面板/组件之间的解耦通信。
 *
 * Usage:
 *   var bus = new GitDoc.EventBus();
 *   bus.on("rollback:confirm", function(data) { ... });
 *   bus.emit("rollback:confirm", { hash: "abc123" });
 *   bus.off("rollback:confirm", handlerFn);
 */
var GitDoc = GitDoc || {};

(function(ns) {
    'use strict';

    /**
     * @constructor
     */
    function EventBus() {
        this._listeners = {};
    }

    EventBus.prototype = {
        /**
         * Register an event listener.
         * @param {string} event — Event name (e.g. "rollback:confirm").
         * @param {Function} callback — Handler function.
         */
        on: function(event, callback) {
            if (!this._listeners[event]) {
                this._listeners[event] = [];
            }
            this._listeners[event].push(callback);
        },

        /**
         * Remove an event listener.
         * @param {string} event — Event name.
         * @param {Function} callback — The specific handler to remove.
         */
        off: function(event, callback) {
            var list = this._listeners[event];
            if (!list) return;
            var idx = list.indexOf(callback);
            if (idx !== -1) {
                list.splice(idx, 1);
            }
        },

        /**
         * Emit an event to all registered listeners.
         * @param {string} event — Event name.
         * @param {*} data — Data payload passed to each handler.
         */
        emit: function(event, data) {
            var list = this._listeners[event];
            if (!list) return;
            for (var i = 0; i < list.length; i++) {
                try {
                    list[i](data);
                } catch (e) {
                    console.error("[GitDoc.EventBus] Error in handler for '" + event + "':", e);
                }
            }
        },

        /**
         * Remove all listeners (for cleanup).
         */
        clear: function() {
            this._listeners = {};
        }
    };

    ns.EventBus = EventBus;

})(GitDoc);
