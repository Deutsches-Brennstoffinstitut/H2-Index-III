class ModelError(Exception):
    pass
class PortError(ModelError):
    pass
class PortEnergyError(PortError):
    pass
class PortMassError(PortError):
    pass
class ComponentError(ModelError):
    pass
class BranchError(ModelError):
    pass
class BranchConnectionError(BranchError):
    pass
class CostFuncError(Exception):
    pass
class DataClassError(Exception):
    pass
class EconomicDataClassError(DataClassError):
    pass
class ExportDataClassError(DataClassError):
    pass
class TechnicalDataClassError(DataClassError):
    pass