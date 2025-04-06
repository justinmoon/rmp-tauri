#!/usr/bin/env bash
set -x

bun install
cargo tauri build

