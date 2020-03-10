;; -*-emacs-lisp-*-
;;
;; Emacs startup file for the Debian GNU/Linux cmake package

(if (file-exists-p "/usr/share/emacs/site-lisp/cmake-mode.el")
 (progn
  (debian-pkg-add-load-path-item (concat "/usr/share/"
                                  (symbol-name debian-emacs-flavor)
                                  "/site-lisp/cmake-data"))
  (autoload 'cmake-mode "cmake-mode")
  (setq auto-mode-alist
   (append '(("CMakeLists\\.txt\\'" . cmake-mode)
             ("\\.cmake\\'" . cmake-mode))
    auto-mode-alist)))
 (message "cmake-data removed but not purged, skipping setup"))
