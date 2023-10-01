{ pkgs ? import <nixpkgs> {} }:

let
	python = pkgs.python3.withPackages (ps: with ps; [
		black
	]);
in

pkgs.mkShell {
	buildInputs = with pkgs; [
		python
		pyright
		sqlite
		sqlfluff
		litecli
	];

	shellHook = ''
		python3 -m venv .venv
		source .venv/bin/activate
	'';
}
