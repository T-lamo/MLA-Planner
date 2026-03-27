import { defineStore } from 'pinia'
import { BaseRepository } from '../repositories/BaseRepository'

export interface RoleRead {
  id: string
  libelle: string
}

export interface PermissionCodeRead {
  id: string
  code: string
}

export interface RoleWithPermissions {
  id: string
  libelle: string
  permissions: PermissionCodeRead[]
}

class AdminRepository extends BaseRepository {
  async getRoles(): Promise<RoleRead[]> {
    const { data } = await this.apiRequest<RoleRead[]>('/roles/')
    return data ?? []
  }

  async getRolesWithPermissions(): Promise<RoleWithPermissions[]> {
    const { data } = await this.apiRequest<RoleWithPermissions[]>('/admin/roles')
    return data ?? []
  }

  async getCapabilities(): Promise<PermissionCodeRead[]> {
    const { data } = await this.apiRequest<PermissionCodeRead[]>('/admin/capabilities')
    return data ?? []
  }

  async updateRolePermissions(
    roleId: string,
    permissionCodes: string[],
  ): Promise<RoleWithPermissions> {
    const { data } = await this.apiRequest<RoleWithPermissions>(
      `/admin/roles/${roleId}/permissions`,
      { method: 'PATCH', body: { permission_codes: permissionCodes } },
    )
    if (!data) throw new Error('Mise à jour des permissions échouée')
    return data
  }

  async createRole(libelle: string): Promise<RoleWithPermissions> {
    const { data } = await this.apiRequest<RoleWithPermissions>('/admin/roles', {
      method: 'POST',
      body: { libelle },
    })
    if (!data) throw new Error('Création du rôle échouée')
    return data
  }

  async deleteRole(roleId: string): Promise<void> {
    await this.apiRequest(`/admin/roles/${roleId}`, { method: 'DELETE' })
  }

  async createCapability(code: string, description?: string): Promise<PermissionCodeRead> {
    const { data } = await this.apiRequest<PermissionCodeRead>('/admin/capabilities', {
      method: 'POST',
      body: { code, description },
    })
    if (!data) throw new Error('Création de la capability échouée')
    return data
  }

  async deleteCapability(capabilityId: string): Promise<void> {
    await this.apiRequest(`/admin/capabilities/${capabilityId}`, { method: 'DELETE' })
  }
}

const repository = new AdminRepository()

export const useRoleStore = defineStore('roles', () => {
  const items = ref<RoleRead[]>([])
  const rolesWithPermissions = ref<RoleWithPermissions[]>([])
  const capabilities = ref<PermissionCodeRead[]>([])
  const loading = ref(false)
  const saving = ref(false)
  const error = ref<unknown>(null)
  let fetched = false

  async function fetchRoles() {
    if (fetched) return
    loading.value = true
    error.value = null
    try {
      items.value = await repository.getRoles()
      fetched = true
    } catch (e: unknown) {
      error.value = e
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchAdminData() {
    loading.value = true
    error.value = null
    try {
      const [roles, caps] = await Promise.all([
        repository.getRolesWithPermissions(),
        repository.getCapabilities(),
      ])
      rolesWithPermissions.value = roles
      capabilities.value = caps
    } catch (e: unknown) {
      error.value = e
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateRolePermissions(roleId: string, permissionCodes: string[]) {
    saving.value = true
    try {
      const updated = await repository.updateRolePermissions(roleId, permissionCodes)
      const idx = rolesWithPermissions.value.findIndex((r) => r.id === roleId)
      if (idx !== -1) rolesWithPermissions.value[idx] = updated
    } finally {
      saving.value = false
    }
  }

  async function createRole(libelle: string) {
    saving.value = true
    try {
      const created = await repository.createRole(libelle)
      rolesWithPermissions.value.push(created)
      items.value.push({ id: created.id, libelle: created.libelle ?? '' })
      return created
    } finally {
      saving.value = false
    }
  }

  async function deleteRole(roleId: string) {
    await repository.deleteRole(roleId)
    rolesWithPermissions.value = rolesWithPermissions.value.filter((r) => r.id !== roleId)
    items.value = items.value.filter((r) => r.id !== roleId)
  }

  async function createCapability(code: string, description?: string) {
    saving.value = true
    try {
      const created = await repository.createCapability(code, description)
      capabilities.value.push(created)
      capabilities.value.sort((a, b) => a.code.localeCompare(b.code))
      return created
    } finally {
      saving.value = false
    }
  }

  async function deleteCapability(capabilityId: string) {
    await repository.deleteCapability(capabilityId)
    capabilities.value = capabilities.value.filter((c) => c.id !== capabilityId)
  }

  return {
    items,
    rolesWithPermissions,
    capabilities,
    loading,
    saving,
    error,
    fetchRoles,
    fetchAdminData,
    updateRolePermissions,
    createRole,
    deleteRole,
    createCapability,
    deleteCapability,
  }
})
