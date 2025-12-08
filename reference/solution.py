#!/usr/bin/env python3
"""Performance-optimized agent.

Lab 3.3 Deliverable: Demonstrates performance best practices
including caching, parallel execution, timeouts, hints, and fillers.
"""

import time
import concurrent.futures
from functools import lru_cache
from signalwire_agents import AgentBase, SwaigFunctionResult


class OptimizedAgent(AgentBase):
    """Agent with performance optimizations applied."""

    def __init__(self):
        super().__init__(name="optimized-agent")

        # OPTIMIZATION 1: Concise, focused prompts
        self._configure_prompts()
        self._configure_timing()
        self._configure_hints()

        self.add_language("English", "en-US", "rime.spore")
        self._setup_functions()

    def _configure_prompts(self):
        """Concise prompts for better performance."""
        self.prompt_add_section(
            "Role",
            "Customer service agent. Help with products, inventory, shipping."
        )

        self.prompt_add_section(
            "Guidelines",
            bullets=[
                "Be helpful and concise",
                "Confirm before taking actions",
                "Offer alternatives when needed"
            ]
        )

    def _configure_timing(self):
        """OPTIMIZATION 2: Optimized speech timing params."""
        self.set_params({
            "end_of_speech_timeout": 400,  # Slightly faster
            "attention_timeout": 8000,
            "barge_min_words": 2  # Require 2 words to interrupt
        })

    def _configure_hints(self):
        """OPTIMIZATION 3: Speech recognition hints for better accuracy."""
        self.add_hints([
            "product",
            "inventory",
            "shipping",
            "warehouse",
            "SKU",
            "zip code",
            "tracking",
            "order status",
            "delivery"
        ])

    # OPTIMIZATION 4: Cached shipping zone lookup
    @staticmethod
    @lru_cache(maxsize=100)
    def _get_shipping_zone(zip_prefix: str) -> str:
        """Cached zone lookup by zip prefix."""
        zones = {
            "9": "west", "8": "west", "7": "central",
            "6": "central", "5": "central", "4": "central",
            "3": "east", "2": "east", "1": "east", "0": "east"
        }
        return zones.get(zip_prefix, "standard")

    @staticmethod
    @lru_cache(maxsize=100)
    def _get_shipping_rate(zone: str) -> float:
        """Cached shipping rate by zone."""
        rates = {"west": 9.99, "central": 11.99, "east": 12.99, "standard": 14.99}
        return rates.get(zone, 14.99)

    def _check_warehouse(self, warehouse: str) -> int:
        """Simulated warehouse check."""
        time.sleep(0.3)  # Simulated API latency
        inventory = {"A": 10, "B": 5, "C": 15}
        return inventory.get(warehouse, 0)

    def _setup_functions(self):
        """Define optimized functions."""

        # OPTIMIZATION 5: Fillers for slow operations
        @self.tool(
            description="Look up product information",
            parameters={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The product ID to look up"
                    }
                },
                "required": ["product_id"]
            },
            fillers=["Looking that up...", "Checking our catalog..."]
        )
        def get_product(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            product_id = args.get("product_id", "unknown")
            # Fast simulated lookup
            time.sleep(0.3)
            return SwaigFunctionResult(f"Product {product_id}: Widget Pro, $99.99")

        # OPTIMIZATION 6: Parallel warehouse checks
        @self.tool(
            description="Check inventory across warehouses",
            parameters={
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "The SKU to check inventory for"
                    }
                },
                "required": ["sku"]
            },
            fillers=["Checking all warehouses...", "One moment..."]
        )
        def check_inventory(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            sku = args.get("sku", "unknown")
            # Parallel execution - 3 calls in ~0.3s instead of ~1s
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(self._check_warehouse, "A"),
                    executor.submit(self._check_warehouse, "B"),
                    executor.submit(self._check_warehouse, "C")
                ]

                total = 0
                for future in concurrent.futures.as_completed(futures, timeout=2):
                    try:
                        total += future.result()
                    except Exception:
                        pass  # Skip failed warehouse

            return SwaigFunctionResult(f"Inventory for {sku}: {total} total")

        # OPTIMIZATION 7: Cached calculations
        @self.tool(
            description="Calculate shipping cost",
            parameters={
                "type": "object",
                "properties": {
                    "zip_code": {
                        "type": "string",
                        "description": "Destination zip code"
                    },
                    "weight": {
                        "type": "number",
                        "description": "Package weight in pounds"
                    }
                },
                "required": ["zip_code", "weight"]
            },
            fillers=["Calculating shipping..."]
        )
        def calculate_shipping(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            zip_code = args.get("zip_code", "50000")
            weight = args.get("weight", 1.0)
            # Use cached lookups
            zip_prefix = zip_code[0] if zip_code else "5"
            zone = self._get_shipping_zone(zip_prefix)
            base_rate = self._get_shipping_rate(zone)

            # Simple weight calculation
            total = base_rate + (weight * 0.50)

            return SwaigFunctionResult(
                f"Shipping to {zip_code} ({zone} zone): ${total:.2f}"
            )

        @self.tool(
            description="Get shipping zone for zip code",
            parameters={
                "type": "object",
                "properties": {
                    "zip_code": {
                        "type": "string",
                        "description": "Zip code to look up"
                    }
                },
                "required": ["zip_code"]
            }
        )
        def get_shipping_zone(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            zip_code = args.get("zip_code", "50000")
            # Instant from cache after first call
            zone = self._get_shipping_zone(zip_code[0] if zip_code else "5")
            return SwaigFunctionResult(f"Zip {zip_code} is in {zone} zone")

        # OPTIMIZATION 8: Timeout protection
        @self.tool(
            description="Check external service status",
            fillers=["Checking service status..."]
        )
        def check_external_service(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            try:
                # Reasonable timeout
                import requests
                response = requests.get(
                    "https://httpbin.org/get",
                    timeout=2  # 2 second timeout
                )
                return SwaigFunctionResult("External service: Online")
            except Exception:
                return SwaigFunctionResult(
                    "Could not check external service. Please try again."
                )


if __name__ == "__main__":
    agent = OptimizedAgent()
    agent.run()
