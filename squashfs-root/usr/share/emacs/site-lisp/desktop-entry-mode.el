;;; desktop-entry-mode.el --- freedesktop.org desktop entry editing

;; Copyright (C) 2003-2004, 2006-2007 Ville Skyttä, <scop at xemacs.org>

;; Author:   Ville Skyttä, <scop at xemacs.org>
;; Keywords: unix, desktop entry

;; This file is part of XEmacs.

;; XEmacs is free software; you can redistribute it and/or modify it
;; under the terms of the GNU General Public License as published by
;; the Free Software Foundation; either version 2, or (at your option)
;; any later version.

;; XEmacs is distributed in the hope that it will be useful, but
;; WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;; General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with XEmacs; see the file COPYING.  If not, write to the Free
;; Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
;; MA 02110-1301 USA.

;;; Commentary:

;; This mode provides basic functionality, eg. syntax highlighting and
;; validation for freedesktop.org desktop entry files.
;;
;; To install it:
;;
;;   In XEmacs:
;;   Just install the XEmacs `text-modes' package, this mode is included.
;;   See <http://www.xemacs.org/Documentation/packageGuide.html>.
;;
;;   In GNU Emacs:
;;   Place this file in your load path somewhere (eg. site-lisp), and add
;;   the following to your .emacs:
;;
;;   (autoload 'desktop-entry-mode "desktop-entry-mode" "Desktop Entry mode" t)
;;   (add-to-list 'auto-mode-alist
;;                '("\\.desktop\\(\\.in\\)?$" . desktop-entry-mode))
;;   (add-hook 'desktop-entry-mode-hook 'turn-on-font-lock)
;;
;; For more information about desktop entry files, see
;;   <http://www.freedesktop.org/Standards/desktop-entry-spec>
;;
;; This version is up to date with version 1.0 of the specification.

;;; Code:

(eval-when-compile
  (require 'regexp-opt))

(defconst desktop-entry-mode-version "1.0 (spec 1.0)"
  "Version of `desktop-entry-mode'.")

(defgroup desktop-entry nil
  "Support for editing freedesktop.org desktop entry files."
  :group 'languages)

(defcustom desktop-entry-validate-command "desktop-file-validate"
  "*Command for validating desktop entry files."
  :type 'string
  :group 'desktop-entry)

(defgroup desktop-entry-faces nil
  "Font lock faces for `desktop-entry-mode'."
  :prefix "desktop-entry-"
  :group 'desktop-entry
  :group 'faces)

(defface desktop-entry-group-header-face
  '((((class color) (background light)) (:foreground "mediumblue" :bold t))
    (((class color) (background dark)) (:foreground "lightblue" :bold t))
    (t (:bold t)))
  "*Face for highlighting desktop entry group headers."
  :group 'desktop-entry-faces)

(defface desktop-entry-deprecated-keyword-face
  '((((class color)) (:background "yellow" :foreground "black" :strikethru t))
    )
  "*Face for highlighting deprecated desktop entry keys."
  :group 'desktop-entry-faces)

(defface desktop-entry-unknown-keyword-face
  '((((class color)) (:foreground "red3" :underline t))
    (t (:underline t))
    )
  "*Face for highlighting unknown desktop entry keys."
  :group 'desktop-entry-faces)

(defface desktop-entry-value-face
  '((((class color) (background light)) (:foreground "darkgreen"))
    (((class color) (background dark)) (:foreground "lightgreen"))
    )
  "*Face for highlighting desktop entry values."
  :group 'desktop-entry-faces)

(defface desktop-entry-locale-face
  '((((class color) (background light)) (:foreground "dimgray"))
    (((class color) (background dark)) (:foreground "lightgray"))
    )
  "*Face for highlighting desktop entry locales."
  :group 'desktop-entry-faces)

(defconst desktop-entry-keywords
  (eval-when-compile
    (concat
     "\\(?:"
     (regexp-opt
      '(
        "Type"
        "Version"
        "Name"
        "GenericName"
        "NoDisplay"
        "Comment"
        "Icon"
        "Hidden"
        "OnlyShowIn"
        "NotShowIn"
        "TryExec"
        "Exec"
        "Path"
        "Terminal"
        "MimeType"
        "Categories"
        "StartupNotify"
        "StartupWMClass"
        "URL"
        ;; Reserved for use with KDE
        "ServiceTypes"
        "DocPath"
        "KeyWords"
        "InitialPreference"
        ;; Used by KDE for entries of the FSDevice type
        "Dev"
        "FSType"
        "MountPoint"
        "ReadOnly"
        "UnmountIcon"
        ) 'words)
     "\\|X-[A-Za-z0-9-]+\\)"))
  "Expression for matching desktop entry keys.")

(defconst desktop-entry-deprecated-keywords
  (eval-when-compile
    (concat
     "\\(\\<Type\\s-*=\\s-*MimeType\\>\\|"
     (regexp-opt
      '(
        "Patterns"
        "DefaultApp"
        "Encoding"
        "MiniIcon"
        "TerminalOptions"
        "Protocols"
        "Extensions"
        "BinaryPattern"
        "MapNotify"
        "SwallowTitle"
        "SwallowExec"
        "SortOrder"
        "FilePattern"
        ) 'words)
     "\\)"))
  "Expression for matching deprecated desktop entry keys.")

(defconst desktop-entry-group-header-re
  "^\\[\\(X-[^\][]+\\|\\(?:Desktop \\(?:Entry\\|Action [a-zA-Z]+\\)\\)\\)\\]"
  "Regular expression for matching desktop entry group headers.")

(defconst desktop-entry-font-lock-keywords
  (list
   (cons "^\\s-*#.*$" '(0 'font-lock-comment-face))
   (cons (concat "^" desktop-entry-deprecated-keywords)
         '(0 'desktop-entry-deprecated-keyword-face))
   (cons (concat "^" desktop-entry-keywords) '(0 'font-lock-keyword-face))
   (cons "^[A-Za-z0-9-]+" '(0 'desktop-entry-unknown-keyword-face))
   (cons desktop-entry-group-header-re '(1 'desktop-entry-group-header-face))
   (cons "^[A-Za-z0-9-]+?\\s-*=\\s-*\\(.*\\)"
         '(1 'desktop-entry-value-face))
   (cons "^[A-Za-z0-9-]+?\\[\\([^\]]+\\)\\]\\s-*=\\s-*\\(.*\\)"
         '((1 'desktop-entry-locale-face)
           (2 'desktop-entry-value-face)))
   )
  "Highlighting rules for `desktop-entry-mode' buffers.")

(defvar desktop-entry-imenu-generic-expression
  `((nil ,desktop-entry-group-header-re 1))
  "Imenu generic expression for `desktop-entry-mode'.
See `imenu-generic-expression'.")

;;;###autoload
(defun desktop-entry-mode ()
  "Major mode for editing freedesktop.org desktop entry files.
See <http://www.freedesktop.org/Standards/desktop-entry-spec> for more
information.  See `desktop-entry-mode-version' for information about which
version of the specification this mode is up to date with.

Turning on desktop entry mode calls the value of the variable
`desktop-entry-mode-hook' with no args, if that value is non-nil."
  (interactive)
  (set (make-local-variable 'imenu-generic-expression)
       '((nil "^\\s-*\\(.*\\)\\s-*=" 1)))
  (set (make-local-variable 'compile-command)
       (concat desktop-entry-validate-command " " buffer-file-name))
  (set (make-local-variable 'compilation-buffer-name-function)
       (lambda (x) (concat "*desktop-file-validate "
                           (file-name-nondirectory buffer-file-name) "*")))
  (set (make-local-variable 'comment-start) "# ")
  (set (make-local-variable 'comment-end) "")
  (set (make-local-variable 'comment-start-skip) "#+ *")
  (setq major-mode 'desktop-entry-mode mode-name "Desktop Entry")
  (set (make-local-variable 'imenu-generic-expression)
       desktop-entry-imenu-generic-expression)
  (unless (featurep 'xemacs) ;; font-lock support for GNU Emacs
    (set (make-local-variable 'font-lock-defaults)
         '(desktop-entry-font-lock-keywords)))
  (run-hooks 'desktop-entry-mode-hook))

(defun desktop-entry-validate ()
  "Validate desktop entry in the current buffer."
  (interactive)
  (require 'compile)
  (compile compile-command))

;;;###autoload(add-to-list 'auto-mode-alist '("\\.desktop\\(\\.in\\)?$" . desktop-entry-mode))

(provide 'desktop-entry-mode)

;;; desktop-entry-mode.el ends here
