import logging
from typing import Any

from .constants import PTP_MOVJ, PTP_MOVL

logger = logging.getLogger(__name__)


class Motion:
    """Comandos de movimento do robô."""

    def __init__(self, robot: Any) -> None:
        self.robot = robot

    async def home(self) -> Any:
        """Move o robô para a posição de home."""
        logger.info("Moving to home position")
        return await self.robot.command(
            "set_homecmd"
        )

    async def movj(self, x: float, y: float, z: float, r: float = 0) -> Any:
        """Move o robô no modo PTP MovJ (movimento por articulação).

        Args:
            x: Posição X em mm.
            y: Posição Y em mm.
            z: Posição Z em mm.
            r: Rotação em graus.
        """
        logger.debug(f"MovJ to ({x}, {y}, {z}, r={r})")
        return await self.robot.command(
            "set_ptpcmd",
            ptp_mode=PTP_MOVJ,
            x=x,
            y=y,
            z=z,
            r=r
        )

    async def movl(self, x: float, y: float, z: float, r: float = 0) -> Any:
        """Move o robô no modo PTP MovL (movimento linear).

        Args:
            x: Posição X em mm.
            y: Posição Y em mm.
            z: Posição Z em mm.
            r: Rotação em graus.
        """
        logger.debug(f"MovL to ({x}, {y}, {z}, r={r})")
        return await self.robot.command(
            "set_ptpcmd",
            ptp_mode=PTP_MOVL,
            x=x,
            y=y,
            z=z,
            r=r
        )
