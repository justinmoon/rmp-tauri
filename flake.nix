{
  description = "Slipbox";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    fenix.url = "github:nix-community/fenix";
    flake-utils.url = "github:numtide/flake-utils";
    justin.url = "github:justinmoon/flakes?rev=f7a9598c9fbdc1a4bc0f0ae63b247c95f2333aba";
  };

  outputs =
    {
      nixpkgs,
      fenix,
      flake-utils,
      justin,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ fenix.overlays.default ];
        };

        rustToolchain = pkgs.fenix.complete.withComponents [
          "cargo"
          "clippy"
          "rust-src"
          "rustc"
          "rustfmt"
        ];

        xcode = justin.lib.xcode {
          inherit pkgs;
          # Includes SetFile which can't be wrapped
          symlinkBin = true;
        };

        hdiutilWrapper = pkgs.writeScriptBin "hdiutil" ''
          #!/bin/sh
          exec /usr/bin/hdiutil "$@"
        '';
        # pkgs.darwin.DarwinTools is another option, which has a compiled sw_vers.
        # But just doing this seems more targeted.
        swVersWrapper = pkgs.writeScriptBin "sw_vers" ''
          #!/bin/sh
          exec /usr/bin/sw_vers "$@"
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            rustToolchain
            pkgs.openssl
            pkgs.pkg-config
            pkgs.bun
            pkgs.just
            pkgs.watchexec
            pkgs.nodePackages.typescript
            pkgs.cargo-tauri
            xcode
            hdiutilWrapper
            swVersWrapper
            pkgs.perl
          ];
        };
      }
    );
}
