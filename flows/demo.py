"""兼容入口。"""

from vision_workflow.flow import FlowRunner, load_flow_module


def main() -> None:
    flow = load_flow_module("config.flow")
    result = FlowRunner(flow, dry_run=True).run()
    print(result.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
