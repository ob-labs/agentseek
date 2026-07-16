# Sample Images

The template already includes a starter image pack at `examples/sample_pack/`.
Use this folder for your own `.jpg`, `.jpeg`, `.png`, or `.webp` files:

```bash
uv run ingest-images examples/sample_images
uv run hybrid-demo
```

If you add `manifest.yml` next to your images, the ingest step uses those captions and tags before falling back to VLM captioning.
