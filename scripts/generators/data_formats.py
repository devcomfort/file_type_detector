"""Data format generators."""

import numpy
import pickle
import sqlite3
import struct
import zipfile
from io import BytesIO

import fastavro
import h5py
import onnx
import pyarrow as pa
import pyarrow.parquet as pq
from google.protobuf import descriptor_pb2
from onnx import TensorProto, helper
from scapy.all import Ether, IP, wrpcap

from ._deterministic import write_zip_str
from .base import BaseGenerator
from . import register


@register
class DataFormatGenerator(BaseGenerator):
    """Generates minimal valid data format files."""

    @property
    def extensions(self) -> list[str]:
        return [
            "sqlite",
            "sqlite3",
            "db",
            "parquet",
            "avro",
            "protobuf",
            "pb",
            "h5",
            "hdf5",
            "npy",
            "npz",
            "onnx",
            "pickle",
            "pkl",
            "pt",
            "pth",
            "pcap",
            "stl",
            "dcm",
        ]

    @property
    def sources(self) -> dict[str, str]:
        return {
            "sqlite": "library:sqlite3",
            "sqlite3": "library:sqlite3",
            "db": "library:sqlite3",
            "parquet": "library:pyarrow",
            "avro": "library:fastavro",
            "protobuf": "library:protobuf",
            "pb": "library:protobuf",
            "h5": "library:h5py",
            "hdf5": "library:h5py",
            "npy": "synthetic:NumPy array header",
            "npz": "library:zipfile",
            "onnx": "library:onnx",
            "pickle": "library:pickle",
            "pkl": "library:pickle",
            "pt": "library:pickle",
            "pth": "library:pickle",
            "pcap": "library:scapy",
            "stl": "library:numpy-stl",
            "dcm": "library:pydicom",
        }

    @property
    def category(self) -> str:
        return "data"

    def generate(self, ext: str) -> bytes:
        generators = {
            "sqlite": self._create_sqlite,
            "sqlite3": self._create_sqlite,
            "db": self._create_sqlite,
            "parquet": self._create_parquet,
            "avro": self._create_avro,
            "protobuf": self._create_protobuf,
            "pb": self._create_protobuf,
            "h5": self._create_h5,
            "hdf5": self._create_h5,
            "npy": self._create_npy,
            "npz": self._create_npz,
            "onnx": self._create_onnx,
            "pickle": self._create_pickle,
            "pkl": self._create_pickle,
            "pt": self._create_pytorch,
            "pth": self._create_pytorch,
            "pcap": self._create_pcap,
            "stl": self._create_stl,
            "dcm": self._create_dcm,
        }
        return generators[ext]()

    def _create_sqlite(self) -> bytes:
        import tempfile
        import os

        fd, tmp_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            conn = sqlite3.connect(tmp_path)
            conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO sample (name) VALUES ('test')")
            conn.commit()
            conn.close()
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp_path)

    def _create_parquet(self) -> bytes:
        buf = BytesIO()
        table = pa.table({"id": [1], "name": ["test"]})
        pq.write_table(table, buf)
        return buf.getvalue()

    def _create_avro(self) -> bytes:
        schema = {
            "type": "record",
            "name": "Sample",
            "fields": [
                {"name": "id", "type": "int"},
                {"name": "name", "type": "string"},
            ],
        }
        buf = BytesIO()
        fastavro.writer(
            buf,
            schema,
            [{"id": 1, "name": "test"}],
            sync_marker=b"\x00" * 16,
        )
        return buf.getvalue()

    def _create_protobuf(self) -> bytes:
        file_desc = descriptor_pb2.FileDescriptorProto()
        file_desc.name = "sample.proto"
        file_desc.syntax = "proto3"
        msg = file_desc.message_type.add()
        msg.name = "Sample"
        field = msg.field.add()
        field.name = "id"
        field.number = 1
        field.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT32
        return file_desc.SerializeToString()

    def _create_h5(self) -> bytes:
        buf = BytesIO()
        with h5py.File(buf, "w") as f:
            f.create_dataset("data", data=[1.0])
        return buf.getvalue()

    def _create_npy(self) -> bytes:
        return (
            b"\x93NUMPY"
            + struct.pack("<BB", 1, 0)
            + struct.pack("<H", 10)
            + b"{'descr': '<f8', 'fortran_order': False, 'shape': (1,), }"
            + b"\n"
            + struct.pack("<d", 1.0)
        )

    def _create_npz(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(zf, "arr_0.npy", b"\x93NUMPY" + b"\x00" * 20)
        return buf.getvalue()

    def _create_onnx(self) -> bytes:
        buf = BytesIO()
        X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [1])
        Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1])
        node = helper.make_node("Identity", ["X"], ["Y"])
        graph = helper.make_graph([node], "test", [X], [Y])
        model = helper.make_model(graph)
        model.opset_import[0].version = 1
        onnx.save(model, buf)
        return buf.getvalue()

    def _create_pickle(self) -> bytes:
        return pickle.dumps({"sample": "data"})

    def _create_pytorch(self) -> bytes:
        buf = BytesIO()
        buf.write(b"PK\x03\x04")
        pickle.dump({"sample": "data"}, buf)
        return buf.getvalue()

    def _create_pcap(self) -> bytes:
        import io

        from scapy.all import PcapWriter

        pkt = Ether() / IP()
        pkt.time = 1700000000  # fixed epoch for reproducibility
        buf = io.BytesIO()
        writer = PcapWriter(buf, linktype=1, nano=False, sync=True)
        writer.write(pkt)
        writer.flush()
        return buf.getvalue()

    def _create_stl(self) -> bytes:
        from stl import mesh
        import tempfile
        import os

        vertices = numpy.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = numpy.array([[0, 1, 2]])
        stl_mesh = mesh.Mesh(numpy.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                stl_mesh.vectors[i][j] = vertices[f[j]]
        fd, tmp_path = tempfile.mkstemp(suffix=".stl")
        os.close(fd)
        try:
            stl_mesh.save(tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp_path)

    def _create_dcm(self) -> bytes:
        import pydicom
        from pydicom.dataset import Dataset, FileMetaDataset
        from pydicom.uid import ExplicitVRLittleEndian

        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
        file_meta.MediaStorageSOPInstanceUID = "1.2.3.4.5"
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        ds = Dataset(file_meta=file_meta)
        ds.PatientName = "Test"
        buf = BytesIO()
        pydicom.dcmwrite(buf, ds, implicit_vr=False, little_endian=True)
        return buf.getvalue()
