import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useAccountStore = defineStore('accounts', () => {
  const accounts = ref([])
  const currentAccount = ref(null)

  async function fetchAccounts() {
    try {
      const response = await api.get('/accounts')
      if (response.data.success) {
        accounts.value = response.data.data
        if (accounts.value.length > 0 && !currentAccount.value) {
          currentAccount.value = accounts.value[0].id
        }
      }
    } catch (error) {
      console.error('获取账户失败:', error)
    }
  }

  function setCurrentAccount(accountId) {
    currentAccount.value = accountId || null
  }

  async function createAccount(data) {
    try {
      const response = await api.post('/accounts', data)
      if (response.data.success) {
        await fetchAccounts()
        return { success: true, data: response.data.data }
      }
      return { success: false, message: response.data.message }
    } catch (error) {
      return { success: false, message: error.response?.data?.message || '创建失败' }
    }
  }

  async function updateAccount(id, data) {
    try {
      const response = await api.put(`/accounts/${id}`, data)
      if (response.data.success) {
        await fetchAccounts()
        return { success: true }
      }
      return { success: false, message: response.data.message }
    } catch (error) {
      return { success: false, message: error.response?.data?.message || '更新失败' }
    }
  }

  async function deleteAccount(id) {
    try {
      const response = await api.delete(`/accounts/${id}`)
      if (response.data.success) {
        await fetchAccounts()
        return { success: true }
      }
      return { success: false, message: response.data.message }
    } catch (error) {
      return { success: false, message: error.response?.data?.message || '删除失败' }
    }
  }

  return {
    accounts,
    currentAccount,
    fetchAccounts,
    setCurrentAccount,
    createAccount,
    updateAccount,
    deleteAccount
  }
})