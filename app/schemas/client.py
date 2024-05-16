# from typing import Optional
# from datetime import datetime
# from pydantic import BaseModel, field_validator, model_validator,validators,validator
# import subprocess
# from app.core.Settings import get_settings
# import uuid

# setttings = get_settings()


# class ClientBase(BaseModel):
# 	# id: Optional[uuid.uuid4] = None
# 	name: Optional[str] = None
# 	enabled: Optional[bool] = None
# 	address: Optional[str] = None
# 	public_key: Optional[str] = None
# 	privateKey: Optional[str] = None
# 	preSharedKey: Optional[str] = None
# 	created_at: Optional[datetime] = None
# 	updated_at: Optional[datetime] = None
# 	persistentKeepalive: Optional[int] = None
# 	latestHandshakeAt: Optional[datetime] = None
# 	transferRx: Optional[int] = None
# 	transferTx: Optional[int] = None
#
# 	# allowedIPs: Optional[list[str]] = None
#
# 	class Config:
# 		from_attributes = True
	
	# @field_validator("allowedIPs", mode="before")
	# @classmethod
	# def str_to_ip(cls, v):
	#     if isinstance(v, str):
	#         return v.split(",")
	#     return v
	
	# @model_validator(mode="before")
	# def check_transferRx(self):
	# 	if self.transferRx is None or not isinstance(self.transferRx, int):
	# 		v = 0
	# 	return v
	# @field_validator("transferTx", mode="before")
	# @classmethod
	# def check_transferTx(cls, v):
	# 	if v is None or not isinstance(v, int):
	# 		v = 0
	# 	return v


# class ClientCreate(ClientBase):
# 	name: str
#
# 	@model_validator(mode="after")
# 	def verify_fields(self):
# 		self.enabled = True
# 		command = ["wg", "pubkey"]
# 		self.privateKey = (
# 			subprocess.run(["wg", "genkey"], stdout=subprocess.PIPE)
# 			.stdout.decode()
# 			.strip()
# 		)
# 		proc = subprocess.Popen(
# 			command,
# 			stdin=subprocess.PIPE,
# 			stdout=subprocess.PIPE,
# 			stderr=subprocess.PIPE,
# 			# executable='/bin/bash'
# 		)
# 		privateToBytes = bytes(self.privateKey, "utf-8")
# 		(stdoutData, stderrData) = proc.communicate(privateToBytes)
# 		self.public_key = stdoutData.decode().strip()
# 		self.preSharedKey = (
# 			subprocess.run(
# 				["wg", "genpsk"],
# 				stdin=subprocess.PIPE,
# 				stdout=subprocess.PIPE,
# 				stderr=subprocess.PIPE,
# 				# executable='/bin/bash'
# 			)
# 			.stdout.decode()
# 			.strip()
# 		)
# 		return self


# class ClientUpdate(ClientBase):
# 	name: Optional[str] = None
# 	enabled: Optional[bool] = None


# class ClientInDBBase(ClientBase):
# 	id: uuid.UUID
# 	interface_id: int
# 	created_at: datetime
# 	privateKey: str
# 	public_key: str
# 	preSharedKey: str
#
# 	class Config:
# 		from_attributes = True


# Additional properties to return via API
# class ClientOut(ClientInDBBase):
# 	downloadableConfig: Optional[bool] = False
# 	transferRx: Optional[int] = 0
# 	transferTx: Optional[int] = 0
# 	allowedIPs: Optional[str] = "0.0.0.0/0, ::/0"
# 	latestHandshakeAt: Optional[datetime] = None
# 	persistentKeepalive: Optional[int] = None
# 	created_at: datetime
# 	updated_at: Optional[datetime] = None
#
# 	@model_validator( mode="after")
# 	def check_downloadableConfig(self):
# 		if self.privateKey:
# 			self.downloadableConfig = True
# 		return self

